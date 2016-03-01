A SaltStack module for Zimbra 8 configuration management. 

It uses LDAP or the filesystem for reads, which is drastically faster than running zmprov/zmlocalconfig directly. However, zmprov/zmlocalconfig is still used for writes for reliability. 

### Sample module usage:

- Gets the value for the given localconfig: `salt '*' zimbra.get_localconfig mysql_root_password`
- Sets the value for the given localconfig: `salt '*' zimbra.set_localconfig antispam_enable_rule_updates true`
- Run a zmprov command : `salt '*' zimbra.zmprov "createAccount someone@domain.com somepass"`
- Check if a zimlet is enabled in a COS: `salt '*' zimbra.zimletCosEnabled com_zimbra_phone default`


### Sample state usage: 

See [sample.sls](sample.sls) for more examples, but here are a few:

```
# Enable icon-flashing for new mail:
default_newmail_flash_icon:
  zimbra.modifyCos:
    - name: 'zimbraPrefMailFlashIcon'
    - cos: 'default'
    - value: 'TRUE'

# Disable phone Zimlet:
disable_phone_zimlet:
  zimbra.disableZimletCos:
    - name: 'com_zimbra_phone'
    - cos: 'default'

# Block file extensions in attachments:
{% for ext in [ 'bat', 'cab', 'chm', 'cmd', 'com', 'exe', 'hlp', 
'jar', 'pif', 'reg', 'scr', 'vbe', 'vbs', 'vbx'  ] %}
global_block_extension_{{ext}}:
  zimbra.modifyConfig:
    - name: '+zimbraMtaBlockedExtension'
    - value: {{ext}}
{% endfor %}

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

# Enable antispam rule updates
antispam_enable_rule_updates:
  zimbra.zmlocalconfig:
    - name: 'antispam_enable_rule_updates'
    - value: 'true'
```




