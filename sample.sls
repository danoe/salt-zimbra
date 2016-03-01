# Sample usage of this salt-zimbra module:

create_rizvir_account:
  zimbra.createAccount:
    - name: 'rizvir@test.com'
    - password: 'thepass'
    - sn: 'Rizvi R'
    - displayName: 'Rizvi R'
    - description: 'Some description here'


# Enable icon-flashing for new mail:
default_newmail_flash_icon:
  zimbra.modifyCos:
    - name: 'zimbraPrefMailFlashIcon'
    - cos: 'default'
    - value: 'TRUE'


# Correct timezone based on pillar, or a default:
#
default_timezone:
  zimbra.modifyCos:
    - name: 'zimbraPrefTimeZoneId'
    - cos: 'default'
    - value: {{ salt['pillar.get']('zimbra:timezone', 'Asia/Muscat') }}


# Disable phone Zimlet:
disable_phone_zimlet:
  zimbra.disableZimletCos:
    - name: 'com_zimbra_phone'
    - cos: 'default'


# Set global settings
global_default_domain:
  zimbra.modifyConfig:
    - name: 'zimbraDefaultDomainName'
    - value: {{ primary_domain }}


global_disable_send_blocked_notification:
  zimbra.modifyConfig:
    - name: 'zimbraMtaBlockedExtensionWarnRecipient'
    - value: 'FALSE'


# Block file extensions in attachments:
{% for ext in [ 'bat', 'cab', 'chm', 'cmd', 'com', 'exe', 'hlp', 
'jar', 'pif', 'reg', 'scr', 'vbe', 'vbs', 'vbx'  ] %}
global_block_extension_{{ext}}:
  zimbra.modifyConfig:
    - name: '+zimbraMtaBlockedExtension'
    - value: {{ext}}
{% endfor %}


# Create an alias from admin@fqdn.domain.com to admin@primary.com
# so that we just need use 'admin' as the username to log in
create_admin_alias:
  zimbra.createAlias:
    - name: admin@{{ primary_domain }}
    - original: admin@{{ grains['fqdn'] }}
 

# zimbra ms ... example
# Workaround for https://bugzilla.zimbra.com/show_bug.cgi?id=80563
disable_proxy_upstream_ssl:
  zimbra.modifyServer:
    - name: 'zimbraReverseProxySSLToUpstreamEnabled'
    - server: {{ grains['fqdn'] }}
    - value: 'FALSE'


# Enable volume compression
# after a fresh zimbra install, the volume is 1
enable_volume_compression:
  zimbra.compressVolume:
    - name: '1'


# Zimbra 8 has this wonderful feature of automatic spam definition updates (missing in 
# Zimbra 7), but it's disabled by default, so enable it (antispam_enable_restarts will 
# restart amavis in the night if there is a spam definition update)
antispam_enable_rule_updates:
  zimbra.zmlocalconfig:
    - name: 'antispam_enable_rule_updates'
    - value: 'true'
antispam_enable_restarts:
  zimbra.zmlocalconfig:
    - name: 'antispam_enable_restarts'
    - value: 'true'
antispam_enable_rule_compilation:
  zimbra.zmlocalconfig:
    - name: 'antispam_enable_rule_compilation'
    - value: 'true'


