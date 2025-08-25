frappe.ui.form.on("Purchase Order", {
    setup: function(frm) {
        frm.set_query("custom_supplier_quotation_ref", "items", function(doc, cdt, cdn) {
            return {
                filters : {
                    "custom_quotation_status": "Selected",
                    "status" : "Submitted"
                },
            };
        })  
    }
})