'''
Zimbra execution module
Uses LDAP or the filesystem for reads, which is drastically faster than 
running zmprov/zmlocalconfig directly. However, zmprov/zmlocalconfig is
still used for writes. 
'''

from salt.exceptions import SaltInvocationError, CommandExecutionError

import xml.etree.ElementTree as ET
try:
    import ldap
    HAS_LDAP = True
except ImportError:
    HAS_LDAP = False

from pagedLDAP import PagedLDAPObject

# Parse localconfig XML tree
localconfig_xml = ET.parse('/opt/zimbra/conf/localconfig.xml')
localconfig_root = localconfig_xml.getroot()

def get_localconfig(name):
    '''
    Gets the value for the given localconfig

    CLI Example:
    .. code-block:: bash
       
        salt '*' zimbra.get_localconfig mysql_root_password
    '''
    
    try :
        value = localconfig_root.findall("./*[@name='{0}']/value".format(name))[0].text
    except:
        value = None

    return value


# Global 'l' ldap object used everywhere:
try: 
    ldap_master_url = get_localconfig('ldap_master_url')
    ldap_bind_dn = get_localconfig('zimbra_ldap_userdn')
    ldap_bind_password = get_localconfig('zimbra_ldap_password')
    ldap_starttls_supported = get_localconfig('ldap_starttls_supported')
    ldap_starttls_required = get_localconfig('zimbra_require_interprocess_security')
    l = PagedLDAPObject(ldap_master_url)
    l.set_option(ldap.OPT_X_TLS_CACERTDIR, '/opt/zimbra/conf/ca')
    # force the creation of a new TLS context. This must be the last TLS option.
    # see: http://stackoverflow.com/a/27713355/298479
    l.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    if ldap_starttls_supported == "1" and ldap_starttls_required == "1":
        l.start_tls_s()
    l.simple_bind_s(ldap_bind_dn, ldap_bind_password)
    ldap_success = True
except:
    ldap_success = False
   


def __virtual__():
    if HAS_LDAP and ldap_success:
        return "zimbra"
    elif not HAS_LDAP:
        return False,['zimbra needs the python-ldap rpm to function']
    else:
        return False,['Could not bind to LDAP']



def ldap_exists(base, name):
    '''
    Checks Zimbras LDAP for the filter specified in name
    Returns true if found, otherwise returns false

    CLI Example:
    .. code-block:: bash

        salt '*' zimbra.ldap_exists base='cn=something' '(zimbraDomainName=test-webui.lan)'
    '''

    results = l.search_st(base, ldap.SCOPE_SUBTREE, name, attrsonly=1)

    if len(results) > 0:
        return True
    return False


def ldap_get(base, name):
    '''
    Returns a list of values of the given key, searching in the given base DN. If you're using this on the command
    line, you will need to specify base= and name= explicitly, since base contains an equal sign

    CLI Example:
    .. code-block:: bash

        salt '*' zimbra.ldap_get base='cn=config,cn=zimbra' zimbraImapMaxConnections
    '''
    
    results = l.paged_search_ext_s(base, ldap.SCOPE_SUBTREE, '({0}=*)'.format(name), [ name ])

    if len(results) == 0:
        return False

    return results[0][1][name]


def zmprov(arguments):
    '''
    Runs zmprov with the given arguments, and returns True if it worked, or False if it did not.
    
    CLI Example:
    .. code-block:: bash

        salt '*' zimbra.zmprov "createAccount someone@domain.com somepass"
    '''
    
    command = '/opt/zimbra/bin/zmprov {0}'.format(arguments)
    ret = __salt__['cmd.retcode'](cmd=command, runas='zimbra')
    if ret == 0:
        return True
    return False


def set_localconfig(name, value):
    '''
    Sets the given zmlocalconfig key with the given value
    
    CLI Example:
    .. code-block:: bash

        salt '*' zimbra.set_localconfig antispam_enable_rule_updates true
    '''
    
    command = '/opt/zimbra/bin/zmlocalconfig -e {0}={1}'.format(name, value)
    ret = __salt__['cmd.retcode'](cmd=command, runas='zimbra')
    if ret == 0:
        return True
    return False
 
def zimletCosEnabled(name, cos):
    '''
    Returns True if the zimlet name is enabled in that cos
    
    Example:
    .. code-block:: bash
    
        salt '*' zimbra.zimletCosEnabled com_zimbra_phone default

    '''
    values = ldap_get('cn={cos},cn=cos,cn=zimbra'.format(cos=cos), 'zimbraZimletAvailableZimlets')
    
    # Check if +com_zimbra_thezimlet exists in values:
    for line in values:
        if line == ('+{0}'.format(name)):
            return True
    return False
    

def zimletCosEnable(name, cos, enable=False):
    '''
    Disables or enables a particular zimlet in the given cos.
    '''
    action = 'allow' if enable else 'deny'

    command = '/opt/zimbra/bin/zmzimletctl acl {zimlet} {cos} {action}'.format(
            zimlet=name, cos=cos, action=action)

    ret = __salt__['cmd.retcode'](cmd=command, runas='zimbra')
    if ret == 0:
        return True
    return False

    
def is_volume_compressed(vol_id=1):
    # TODO: read only comment, but is slow because we call the java app
    # We need to find a way to get this information without java
    '''
    Returns true if the given volume is compressed, otherwise returns False
    '''
    command = '/opt/zimbra/bin/zmvolume --list --id {0}'.format(vol_id)

    output = __salt__['cmd.run'](cmd=command, runas='zimbra')
    # output is like:
    #       Volume id: 1                                                                                                                                                          
    #        name: message1
    #        type: primaryMessage
    #        path: /opt/zimbra/store
    #  compressed: false
    #     current: true
    
    for line in output.splitlines():
        if ' compressed: ' in line:
            value = line.split()[1]
            if value == 'false':
                return False
            return True
    raise CommandExecutionError
    return False

def compress_volume(vol_id=1):
    '''
    Runs zmvolume to compress the selected volume
    '''
    command = '/opt/zimbra/bin/zmvolume --edit --id {0} --compress true'.format(vol_id)

    ret = __salt__['cmd.retcode'](cmd=command, runas='zimbra')
    if ret == 0:
        return True
    return False



# vim: set tabstop=4 expandtab:
