import frappe
import erpnext
from frappe.desk.form.load import get_attachments
from frappe import _

# ----------------------- Payment Cycle Customisation -----------------------------
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
        doc.grand_total = pi['outstanding_amount']
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
        po_doc = frappe.get_doc('Purchase Order', reference_docname)
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

def revert_is_payment_req_created_in_po_pi(self, method=None):
    if self.reference_doctype == "Purchase Invoice" or self.reference_doctype == "Purchase Order":
        if self.reference_name != None:
            frappe.db.set_value(self.reference_doctype, self.reference_name, "custom_payment_request_created", "")
            frappe.msgprint("Is Payment Request Created is updated {0} {1}".format(self.reference_doctype, self.reference_name), alert=True)

# ----------------------- Purchase / Buying Cycle Customisation --------------------
def validate_po_conditions(self, method=None):
    if len(self.items) > 0:
        for item in self.items:
            # If Current User Role Is Purchase Master Manager Then Do not Check Any Conditions
            if item.material_request == None and item.supplier_quotation == None and item.custom_supplier_quotation_ref == None:
                purchase_master_manager_role = frappe.db.get_single_value("Shott Settings", "purchase_master_manager")
                user_roles = frappe.get_roles(frappe.session.user)
                print(user_roles)
                if purchase_master_manager_role in user_roles:
                    return
                else:
                    frappe.throw("You are not allowed to create Purchase Order Without Material Request or Supplier Quotation Ref.")

            # Check For Supplier Quotation Is Not Expired And Approved
            if item.supplier_quotation != None or item.custom_supplier_quotation_ref != None:
                supplier_quotation = frappe.get_doc("Supplier Quotation", item.supplier_quotation if item.supplier_quotation != None else item.custom_supplier_quotation_ref)
                if supplier_quotation.status == 'Expired' or supplier_quotation.custom_quotation_status != "Selected":
                    frappe.throw("Cannot create Purchase Order from Supplier Quotation having Status {0} or Quotation Status {1}.".format(frappe.bold("Expired"), frappe.bold("Pending/Rejected")))  
            
            # If PO Is Creaetd As Material Request > Request For Quotation > Supplier Quotation > Purchase Order
            if item.material_request != None and item.supplier_quotation != None:
                item.custom_supplier_quotation_ref = item.supplier_quotation
            
            # If PO Is Created Directly From MR Then Find Its Existing SQ And If Find Set It To Custom SQ Ref Field.
            if item.material_request != None and item.supplier_quotation == None:
                supplier_quotation_ref = frappe.db.get_value("Supplier Quotation Item", {'material_request' : item.material_request}, 'parent')
                if supplier_quotation_ref != None:
                    item.custom_supplier_quotation_ref = supplier_quotation_ref
                # elif supplier_quotation_ref == None:
                #     frappe.throw("Supplier Quotation Is Not Available!")


def fetch_sq_attachments_in_po(self,method=None):
    if len(self.items) > 0:
        supplier_quotation_ref = self.items[0].supplier_quotation or self.items[0].custom_supplier_quotation_ref
        if supplier_quotation_ref != None:
            attachments = get_attachments('Supplier Quotation', supplier_quotation_ref)
            print(attachments)
            if len(attachments) > 0:
                for attach_item in attachments:
                    self.append("custom_sq_attachment_", {
                        'attachment' : attach_item.file_url
                    })
                    self.save(ignore_permissions=True)

                    # save attachments to new doc
                    _file = frappe.get_doc(
                        {
                            "doctype": "File",
                            "file_url": attach_item.file_url,
                            "file_name": attach_item.file_name,
                            "attached_to_name": self.name,
                            "attached_to_doctype": self.doctype,
                            "attached_to_field" : "attachment",
                            "folder": "Home/Attachments",
                            "is_private": attach_item.is_private,
                        }
                    )
                    _file.save(ignore_permissions=True)

@frappe.whitelist()
def change_valid_date_in_supplier_quotation(updated_date, transaction_date, doctype, docname):
    if updated_date != None and doctype != None and docname != None:
        # validate date
        if frappe.utils.getdate(updated_date) < frappe.utils.getdate(transaction_date):
            frappe.throw(_("Valid till Date cannot be before Transaction Date"))
        frappe.db.set_value(doctype, docname, 'valid_till', updated_date)

        # update status based on new date
        if frappe.utils.getdate(updated_date) > frappe.utils.getdate(frappe.utils.nowdate()):
            frappe.db.set_value(doctype, docname, 'status', "Submitted")
        else:
            frappe.db.set_value(doctype, docname, 'status', "Expired")