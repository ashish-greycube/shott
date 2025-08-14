from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.setup_wizard import make_records

def after_migrations():
    custom_fields = {
        "Payment Request" : [
            dict(
                fieldname = 'custom_approved_amount',
                fieldtype = 'Currency',
                label = _('Approved Amount'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'grand_total'
            ),
            dict(
                fieldname = 'custom_attachments',
                fieldtype = 'Data',
                label = _('Attachments'),
                is_custom_field = 1,
                is_system_generated = 0,
                options = 'URL',
                insert_after = 'project'
            ),
            dict(
                fieldname = 'custom_expense_head',
                fieldtype = 'Link',
                label = _('Expense Head'),
                is_custom_field = 1,
                is_system_generated = 0,
                options = 'Account',
                insert_after = 'cost_center'
            ),
            dict(
                fieldname = 'custom_description',
                fieldtype = 'Data',
                label = _('Description'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'custom_expense_head'
            ),
            dict(
                fieldname = 'custom_reason_for_approval_or_rejection',
                fieldtype = 'Small Text',
                label = _('Reason For Approval Or Rejection'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'custom_description',
                depends_on = 'eval:doc.reference_doctype=="Purchase Order";'
            ),
            dict(
                fieldname = 'custom_shott_remark',
                fieldtype = 'Small Text',
                label = _('Shott Remark'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'custom_attachments',
                depends_on = 'eval:doc.reference_doctype=="Purchase Invoice";'
            )
        ],

        "Purchase Order" : [
            dict(
                fieldname = 'custom_payment_request_created',
                fieldtype = 'Select',
                label = _('Is Payment Request Created?'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'custom_rejected',
                options = '\nYes\nNo',
                allow_on_submit = 1
            )
        ],

        "Purchase Invoice" : [
            dict(
                fieldname = 'custom_payment_request_created',
                fieldtype = 'Select',
                label = _('Is Payment Request Created?'),
                is_custom_field = 1,
                is_system_generated = 0,
                insert_after = 'custom_remark',
                options = '\nYes\nNo',
                allow_on_submit = 1
            )
        ]
    }

    print('Creating Custom Fields For Payment Request...')
    for dt, fields in custom_fields.items():
        print("**********\n %s: "% dt, [field.get('fieldname') for field in fields])
    create_custom_fields(custom_fields)