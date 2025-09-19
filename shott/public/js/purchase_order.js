frappe.ui.form.on("Purchase Order", {
    setup: function(frm) {
        frm.set_query("custom_supplier_quotation_ref", "items", function(doc, cdt, cdn) {
            let row = locals[cdt][cdn]
            return {
                query: "shott.api.filter_supplier_quotation_as_per_item_selected",
                filters : {
                    "item" : row.item_code,
                    "custom_quotation_status": "Selected",
                    "status" : "Submitted",
                    "cost_center" : row.cost_center
                },
            };
        })
    }
})