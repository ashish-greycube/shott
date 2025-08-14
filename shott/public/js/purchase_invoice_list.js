frappe.listview_settings['Purchase Invoice'] = {
    onload: function (listview) {
        console.log(listview)
        listview.page.add_action_item(__('Payment Request'), function () {
            createPaymentRequest(listview);
        });
    }
}

function createPaymentRequest(listview) {
    let checkedItems = listview.get_checked_items();
    frappe.call({
        method: "shott.api.createBulkPaymentRequests",
        args: {
            'selectedPIs': checkedItems
        },
        callback: function(res) {
            listview.clear_checked_items()
        }
    });
}