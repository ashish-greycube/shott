import frappe
import erpnext

@frappe.whitelist()
def createBulkPaymentRequests(selectedPIs):
    selectedPIs = frappe.parse_json(selectedPIs)
    print(selectedPIs)
    for pi in selectedPIs:
        refdoc = frappe.get_doc('Purchase Invoice', pi['name'])

        doc = frappe.new_doc("Payment Request")
        doc.payment_request_type = "Outward"
        doc.company =  erpnext.get_default_company()
        doc.reference_doctype = 'Purchase Invoice'
        doc.reference_name = pi['name']
        doc.party_type = 'Supplier',
        doc.party = pi['supplier']
        doc.grand_total = pi['grand_total']
        doc.outstanding_amount = pi['outstanding_amount']
        doc.currency = pi['party_account_currency']
        doc.party_account_currency = pi['party_account_currency']
        doc.cost_center = refdoc.cost_center
        doc.business_unit = refdoc.business_unit

        doc.insert(ignore_permissions=True)
        frappe.msgprint("Payment Request For {0} Is Created: {1}".format(pi['name'], frappe.utils.get_link_to_form("Payment Request", doc.name)), alert=True)

def fetch_custom_details_on_save(self, method = None):
    self.custom_approved_amount = self.grand_total
    
    reference_doctype = self.reference_doctype
    reference_docname = self.reference_name

    custom_attachments = ""
    attachments = frappe.get_all('File', {'attached_to_doctype': reference_doctype, 'attached_to_name' : reference_docname}, ['file_url'])

    if reference_doctype == 'Purchase Invoice' and len(attachments) == 0:
        pi_doc = frappe.get_doc('Purchase Invoice', reference_docname)
        attachments = frappe.get_all('File', {'attached_to_doctype': 'Purchase Order', 'attached_to_name' : pi_doc.items[0].purchase_order}, ['file_url'])

    if len(attachments) == 1:
        custom_attachments = attachments[0].file_url
    elif len(attachments) > 1:
        custom_attachments = f'{frappe.utils.get_url()}/app/file?attached_to_name={reference_docname}&attached_to_doctype={reference_doctype}'

        if reference_doctype == 'Purchase Invoice':
            pi_attachments = frappe.get_all('File', {'attached_to_doctype': reference_doctype, 'attached_to_name' : reference_docname}, ['file_url'])
            if len(pi_attachments) == 0 or pi_attachments == None:
                pi_doc = frappe.get_doc('Purchase Invoice', reference_docname)
                custom_attachments = f'{frappe.utils.get_url()}/app/file?attached_to_name={pi_doc.items[0].purchase_order}&attached_to_doctype=Purchase Order'

    if reference_doctype == 'Purchase Invoice':
        pi_doc = frappe.get_doc('Purchase Invoice', reference_docname)
        self.custom_expense_head = pi_doc.items[0].expense_account
        self.custom_description =  pi_doc.items[0].description
        self.custom_remark = pi_doc.remarks
        self.custom_shott_remark = pi_doc.custom_remark
        self.custom_attachments = custom_attachments

    elif reference_doctype == 'Purchase Order':
        po_doc = frappe.get_doc('Purchase Order', reference_doctype)
        self.custom_expense_head = po_doc.items[0].expense_account
        self.custom_description =  po_doc.items[0].description
        self.custom_reason_for_approval_or_rejection = po_doc.custom_reason_for_approval_or_rejection
        self.custom_remark = po_doc.custom_remarks
        self.custom_attachments = custom_attachments

def update_is_payment_req_created_in_po_pi(self, method=None):
    if self.reference_doctype == "Purchase Invoice" or self.reference_doctype == "Purchase Order":
        if self.reference_name != None:
            frappe.db.set_value(self.reference_doctype, self.reference_name, "custom_payment_request_created", "Yes")
            frappe.msgprint("Is Payment Request Created is updated to YES in {0} {1}".format(self.reference_doctype, self.reference_name), alert=True)