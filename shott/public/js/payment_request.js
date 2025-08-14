frappe.ui.form.on("Payment Request", {
    custom_approved_amount: function (frm) {
        frm.set_value('grand_total', frm.doc.custom_approved_amount)
    }
});