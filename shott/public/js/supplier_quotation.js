frappe.ui.form.on('Supplier Quotation', {
    refresh(frm) {
        if (frm.doc.status == "Expired" || frm.doc.custom_quotation_status == "Pending" || frm.doc.custom_quotation_status == "Rejected") {
            console.log("Hiding Button")
            setTimeout(() => {
                frm.clear_custom_buttons();
                // frm.remove_custom_button('Purchase Order', 'Create');
                // frm.remove_custom_button('Quotation', 'Create');
            }, 100);
        }

        frappe.db.get_doc("Shott Settings").then(doc => {
            let allowed_roles = doc.allow_change_to_valid_date_in_sq
            let res = []
            for (let r in allowed_roles) {
                res.push(allowed_roles[r].role)
            }
            // console.log(res, frappe.user_roles.every(r => frappe.user_roles.includes(r)))
            if (frm.doc.status == "Expired" && frm.doc.custom_quotation_status == "Selected" && frappe.user_roles.every(r => frappe.user_roles.includes(r))) {
                frm.set_df_property('custom_change_validity_btn', 'hidden', 0)
            }
            else if (frm.doc.status != "Expired" || frm.doc.custom_quotation_status != "Selected" || frappe.user_roles.includes(res) === false) {
                frm.set_df_property('custom_change_validity_btn', 'hidden', 1)
            }
        })

        if (frm.is_dirty() == 1) {
            frm.set_df_property('custom_sq_attachment', 'hidden', 1)
        } else {
            frm.set_df_property('custom_sq_attachment', 'hidden', 0)
        }
    },

    custom_change_validity_btn: function (frm) {
        let d = new frappe.ui.Dialog({
            title: "Enter Updated Valid Till Date",
            fields: [
                {
                    label: "Current Valid Till Date",
                    fieldname: 'current_valid_date',
                    fieldtype: 'Date',
                    default: frm.doc.valid_till,
                    read_only: 1
                },
                {
                    label: "Updated Valid Till Date",
                    fieldname: 'updated_valid_date',
                    fieldtype: 'Date',
                }
            ],
            primary_action_label: 'Update',
            primary_action(values) {
                frappe.call({
                    method: "shott.api.change_valid_date_in_supplier_quotation",
                    args: {
                        'updated_date': values.updated_valid_date,
                        'transaction_date': frm.doc.transaction_date,
                        'doctype': frm.doc.doctype,
                        'docname': frm.doc.name
                    },
                    callback: function (res) {
                        frm.reload_doc()
                    }
                })
                d.hide()
            }
        })
        d.show()
    }
});