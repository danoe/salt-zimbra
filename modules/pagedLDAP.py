import ldap
from ldap.controls import SimplePagedResultsControl
from ldap.ldapobject import LDAPObject

class PagedLDAPObject(LDAPObject):
	page_size = 400

	def paged_search_ext_s(self, base, scope, filterstr='(objectClass=*)', attrlist=None, attrsonly=0, serverctrls=None, clientctrls=None, timeout=30, sizelimit=0):

		use_old_paging_api = False

		if hasattr(ldap, 'LDAP_CONTROL_PAGE_OID'):
			use_old_paging_api = True
			lc = SimplePagedResultsControl( ldap.LDAP_CONTROL_PAGE_OID,True,(self.page_size,'') )
			page_ctrl_oid = ldap.LDAP_CONTROL_PAGE_OID
		else:
			lc = ldap.controls.libldap.SimplePagedResultsControl(size=self.page_size,cookie='')
			page_ctrl_oid = ldap.controls.SimplePagedResultsControl.controlType

		msgid = self.search_ext(base, scope, filterstr, attrlist=attrlist, serverctrls=[lc])

		pages = 0
		all_results = []

		while True:
			pages += 1
			rtype, rdata, rmsgid, serverctrls = self.result3(msgid)
			all_results.extend(rdata)
			pctrls = [ c for c in serverctrls if c.controlType == page_ctrl_oid ]
			if pctrls:
				if use_old_paging_api:
					est, cookie = pctrls[0].controlValue
					lc.controlValue = (self.page_size, cookie)
				else:
					cookie = lc.cookie = pctrls[0].cookie

				if cookie:
					msgid = self.search_ext(base, ldap.SCOPE_SUBTREE, filterstr, attrlist=attrlist, serverctrls=[lc])
				else:
					break
			else:
				raise ldap.LDAPError
		return all_results


