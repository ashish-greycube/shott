import frappe
import erpnext
import json
from frappe import _
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
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
            print(item.item_code, item.item_group)
            # If No SQ Then First Check For Exception Item
            if item.supplier_quotation == None and item.custom_supplier_quotation_ref == None:
                print("Checking for exception item........")
                setting_doc = frappe.get_doc("Shott Settings")
                allowed_groups = []
                for group in setting_doc.allowed_item_groups_without_sq:
                    allowed_groups.append(group.item_group)  

                print("allowed groups are : ",allowed_groups)    
                exception_items = frappe.db.get_all(
                    doctype = "Item",
                    filters = {"item_group": ["in", allowed_groups]},
                    fields = ['item_code']
                )   
                allowed_items = []
                
                if len(exception_items) > 0:
                    for r in exception_items:
                        allowed_items.append(r.item_code)
                    print("allowed items are : ",allowed_items)
                    for d in allowed_items:
                        if item.item_code == d:
                            print("Items Matched")
                            return
                    if setting_doc.allow_create_po_without_sq == []:
                        frappe.throw("You are not allowed to create Purchase Order Without Material Request or Supplier Quotation Ref.")

            # If Current User Role Is Purchase Master Manager Then Do not Check Any Conditions
            if item.material_request == None and item.supplier_quotation == None and item.custom_supplier_quotation_ref == None:
                print("Checking for master role........")
                setting_doc = frappe.get_doc("Shott Settings")
                purchase_master_manager_role = []
                for role in setting_doc.allow_create_po_without_sq:
                    purchase_master_manager_role.append(role.role)
                user_roles = frappe.get_roles(frappe.session.user)
                if purchase_master_manager_role == []:
                    frappe.throw("You are not allowed to create Purchase Order Without Material Request or Supplier Quotation Ref.")
                elif purchase_master_manager_role != []:
                    isMaster = False
                    for r in purchase_master_manager_role:
                        for ur in user_roles:
                            if ur == r:
                                isMaster = True
                    if isMaster == True:
                        print("You have master role...Go ahead")
                        return
                    elif isMaster == False:
                        frappe.throw("You are not allowed to create Purchase Order Without Material Request or Supplier Quotation Ref.")
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
            if item.material_request != None and item.supplier_quotation == None and item.custom_supplier_quotation_ref == None:
                supplier_quotation_ref = frappe.db.get_value("Supplier Quotation Item", {'material_request' : item.material_request}, 'parent')
                if supplier_quotation_ref == None:
                    # First Check For Exception Item
                    setting_doc = frappe.get_doc("Shott Settings")
                    allowed_groups = []
                    for group in setting_doc.allowed_item_groups_without_sq:
                        allowed_groups.append(group.item_group)  
    
                    exception_items = frappe.db.get_all(
                        doctype = "Item",
                        filters = {"item_group": ["in", allowed_groups]},
                        fields = ['item_code']
                    )   

                    allowed_items = []
                    if len(exception_items) > 0:
                        for r in exception_items:
                            allowed_items.append(r.item_code)
                        for d in allowed_items:
                            if item.item_code == d:
                                return
                    else:
                        # Item is not in Exception List So Check For Master Role
                        purchase_master_manager_role = []
                        for role in setting_doc.allow_create_po_without_sq:
                            purchase_master_manager_role.append(role.role)
                        user_roles = frappe.get_roles(frappe.session.user)
                        if purchase_master_manager_role == []:
                            frappe.throw("You are not allowed to create Purchase Order Without Supplier Quotation Ref.")
                        elif all(element in user_roles for element in purchase_master_manager_role):
                            return
                        else:
                            frappe.throw("You are not allowed to create Purchase Order Without Supplier Quotation Ref.")
                    frappe.throw("You are not allowed to create Purchase Order Without Supplier Quotation Ref.")

                elif supplier_quotation_ref != None:
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
            
def validate_po_item_with_sq_items(self, method:None):
    if len(self.items) > 0:
        for item in self.items:
            is_valid_sq = False
            is_create_po = False
            if item.custom_supplier_quotation_ref != None or item.supplier_quotation != None:
                supplier_quotation = item.supplier_quotation if item.supplier_quotation != None else item.custom_supplier_quotation_ref
                sq_doc = frappe.get_doc("Supplier Quotation", supplier_quotation)
                if sq_doc != None:
                    # Validation For Supplier In Item Ref Is Same As PO Supplier.
                    if self.supplier != sq_doc.supplier:
                        frappe.throw("At Row {0}: Supplier of given SQ Ref for item {1} is not same as current supplier {2}. Please correct this.".format(item.idx, item.item_code, self.supplier))
                        
                    # Validation For Is Line Item Is Available In SQ Ref + Is Create PO Is Checked For Selected SQ Ref
                    for sq_item in sq_doc.items:
                        if sq_item.item_code == item.item_code:
                            is_valid_sq = True
                            if sq_item.custom_to_create_po == 1:
                                is_create_po = True
                            break
                    if is_create_po == False:
                        frappe.throw("At Row {0}: Item {1} is not marked to Create PO in Supplier Quotation Items {2}".format(item.idx, item.item_code, frappe.utils.get_link_to_form("Supplier Quotation", supplier_quotation)))
                    if is_valid_sq == False:
                        frappe.throw("At Row {0}: Item {1} is not in Supplier Quotation Items {2}".format(item.idx, item.item_code, frappe.utils.get_link_to_form("Supplier Quotation", supplier_quotation)))

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def filter_supplier_quotation_as_per_item_selected(doctype, txt, searchfield, start, page_len, filters):
    sq_list = frappe.db.sql(
        '''
        SELECT sq.name 
        FROM `tabSupplier Quotation` sq 
        INNER JOIN `tabSupplier Quotation Item` sqi 
        ON sq.name = sqi.parent 
        WHERE sq.status = 'Submitted' 
        AND sq.custom_quotation_status = "Selected" 
        AND sqi.custom_to_create_po = 1
        AND sqi.item_code = "{0}"
        AND sqi.cost_center = "{1}"
        AND sq.name  like  %(txt)s ;
        '''.format(filters.get("item"), filters.get("cost_center")), {"txt": "%%%s%%" % txt,}
    )

    return sq_list

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
	if args is None:
		args = {}
	if isinstance(args, str):
		args = json.loads(args)

	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("get_schedule_dates")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	def select_item(d):
		if d.custom_to_create_po == 1:
			print(d)
			filtered_items = args.get("filtered_children", [])
			child_filter = d.name in filtered_items if filtered_items else True
			return child_filter
    
	doclist = get_mapped_doc(
		"Supplier Quotation",
		source_name,
		{
			"Supplier Quotation": {
				"doctype": "Purchase Order",
				"field_no_map": ["transaction_date"],
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Supplier Quotation Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "supplier_quotation_item"],
					["parent", "supplier_quotation"],
					["material_request", "material_request"],
					["material_request_item", "material_request_item"],
					["sales_order", "sales_order"],
				],
				"postprocess": update_item,
				"condition": select_item,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist