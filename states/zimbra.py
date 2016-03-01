'''
Zimbra state
============

This state modules addes some basic Zimbra states. Most of the 
actual work is done via the Zimbra execution module.

Although most salt states uses _underscores_, this state uses
camelCase to match the zmprov commands (so zimbra.createDomain
instead of zimbra.create_domain)

'''

from salt.exceptions import SaltInvocationError, CommandExecutionError

def _zmprovCommand(name, command, arguments, thing, ldapAttribute, ldapValue, ldapBase=""):
    '''
    First checks if '(ldapAttribute=ldapValue)' returns anything, if it does
    then it returns a did-nothing ret dictionary
    
    Otherwise runs "zmprov command arguments", and gives a salt ret dict.
    'thing' is used just as a comment/description (eg. account, domain, etc)

    Eg. command=createAccount, name=test@domain.com, thing=account, 
            ldapAttribute=mail, ldapValue=test@domain.com
    Eg. command=createDomain, name=domain2.com, thing=domain, 
            ldapAttribute=zimbraDomainName, ldapValue=domain2.com
    '''

    name = name.strip()
    
    ret = {'name': name, 'changes': {}, 'result': False, 'command':'' }

    # First check if this already exists
    if __salt__['zimbra.ldap_exists'](ldapBase, '({0}={1})'.format(ldapAttribute, ldapValue)):
        ret['result'] = True
        ret['comment'] = 'The {0} {1} already exists'.format(thing, ldapValue)
        return ret

    # If this is a modify command, check if we can get the old value, if any
    if command.startswith('modify'):
        old_value = __salt__['zimbra.ldap_get'](ldapBase,ldapAttribute)
    else:
        old_value = ''

    ret['changes'] = { command: { 'old':old_value, 'new':ldapValue } }
    ret['comment'] = "zmprov {0} {1}".format(command, arguments)

    # Test=true mode:
    if __opts__['test'] == True:
        ret['result'] = None
        return ret

    # Not a test, and name does not exist, so run the zmprov command
    ret['result'] =  __salt__['zimbra.zmprov']('{0} {1}'.format(command, arguments))
 
    return ret
   

def createDomain(name, zimbraGalMaxResults=500, zimbraGalMode="zimbra"):
    return _zmprovCommand(
        name=name,
        command='createDomain', 
        arguments='{0} zimbraGalMaxResults {zimbraGalMaxResults} zimbraGalMode {zimbraGalMode}'.format(
            name, zimbraGalMaxResults=zimbraGalMaxResults, zimbraGalMode=zimbraGalMode),
        thing='domain',
        ldapAttribute='zimbraDomainName',
        ldapValue=name)


def _stringAttr(attr, value):
    '''
    Returns the string 'attr "value"' if value is set, otherwise just returns a blank string
    '''
    return '{attr} "{value}"'.format(attr=attr,value=value) if value else ""


def createAccount(name, password, givenName="", sn="", displayName="", description="", zimbraHideInGal=True):
    return _zmprovCommand(
        name=name,
        command='createAccount',
        arguments='{account} {password} {givenName} {sn} {description} {displayName} {gal}'.format(
            account=name, password=password, 
            givenName=_stringAttr("givenName", givenName),
            sn=_stringAttr("sn", sn),
            description=_stringAttr("description", description),
            displayName=_stringAttr("displayName", displayName),
            gal="zimbraHideInGal {val}".format(val="TRUE" if zimbraHideInGal else "FALSE"),
        ),
        thing='account',
        ldapAttribute='mail',
        ldapValue=name)


def createAlias(name, original):
    return _zmprovCommand(
        name=name,
        command='addAccountAlias',
        arguments='{account} {alias}'.format(
            account=original, alias=name, 
        ),
        thing='alias',
        ldapAttribute='mail',
        ldapValue=name)


def modifyCos(name, cos, value):
    return _zmprovCommand(
        name=name,
        command='modifyCos',
        arguments='{cos} {attribute} {value}'.format(
            cos=cos, attribute=name, value=value),
        thing='cos',
        ldapBase='cn=default,cn=cos,cn=zimbra',
        ldapAttribute=name,
        ldapValue=value)
        
def disableZimletCos(name, cos):
    ret = {'name': name, 'changes': {}, 'result': False, 'command':'' }
    # First check if it's already disabled
    if not __salt__['zimbra.zimletCosEnabled'](name, cos):
        ret['result'] = True
        ret['comment'] = '{name} is already disabled in the COS {cos}'.format(
            name=name, cos=cos)
        return ret

    # If we reached here, the value is enabled then
    ret['changes'] = { name: { 'old':"Enabled", 'new':"Disabled" } }
    ret['comment'] = "zmzimletctl acl {zimlet} {cos} deny".format(
            zimlet=name, cos=cos)

    # Test=true mode:
    if __opts__['test'] == True:
        ret['result'] = None
        return ret

    # Not a test, run the change
    ret['result'] =  __salt__['zimbra.zimletCosEnable'](name, cos, enable=False)
    return ret


def modifyConfig(name, value):
    return _zmprovCommand(
        name=name,
        command='modifyConfig',
        arguments='{attribute} \"{value}\"'.format(
            attribute=name, value=value),
        thing='config',
        ldapBase='cn=config,cn=zimbra',
        # If 'name' is prefixed with '+', remove it when searching for it:
        ldapAttribute= name.lstrip('+') if name.startswith('+') else name ,
        ldapValue=value)


def modifyServer(name, server, value):
    return _zmprovCommand(
        name=name,
        command='modifyServer',
        arguments='{server} {attribute} {value}'.format(
            server=server, attribute=name, value=value),
        thing='server-config',
        ldapBase='cn={0},cn=servers,cn=zimbra'.format(server),
        # If 'name' is prefixed with '+', remove it when searching for it:
        ldapAttribute= name.lstrip('+') if name.startswith('+') else name ,
        ldapValue=value)


def compressVolume(name):
    # Name is an integer, the volume ID
    vol_id = name
    ret = {'name': name, 'changes': {}, 'result': False, 'command':'' }
    # First check if it's already compressed
    if __salt__['zimbra.is_volume_compressed'](vol_id):
        ret['result'] = True
        ret['comment'] = 'Volume {0} is already compressed'.format(name)
        return ret

    # If we reached here, the volume is not compressed
    ret['changes'] = { name: { 'old':"Compression disabled", 'new':"Compression enabled" } }
    ret['comment'] = "Volume {0} compression will be enabled".format(name)

    # Test=true mode:
    if __opts__['test'] == True:
        ret['result'] = None
        return ret

    # Not a test, run the change
    ret['result'] =  __salt__['zimbra.compress_volume'](vol_id)
    return ret
    
def zmlocalconfig(name, value):
    ret = {'name': name, 'changes': {}, 'result': False, 'command':'' }
    # First check the current value matches 
    current_value = __salt__['zimbra.get_localconfig'](name)
    if current_value == value:
        ret['result'] = True
        ret['comment'] = 'localconfig {0} is already {1}'.format(name, value)
        return ret

    # If we reached here, it needs to be set
    ret['changes'] = { name: { 'old':current_value, 'new':value } }
    ret['comment'] = "zmlocalconfig -e {0}={1}".format(name,value)

    # Test=true mode:
    if __opts__['test'] == True:
        ret['result'] = None
        return ret

    # Not a test, run the change
    ret['result'] =  __salt__['zimbra.set_localconfig'](name,value)
    return ret


# vim: set tabstop=4 expandtab:

