$(".assign-delivery-agent").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('data-url');
    var order_pk = $(this).attr('data-order');
    var agent_pk = $('.delivery_agents').val();
    assignAgent(url,agent_pk,order_pk);
});


$(".order-filter-button").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('data-url');
    var query = $('.order-select-query').val();
    console.log(query);
    window.location.replace(url + "?query=" + query);

});

$('#return_approval_status').change(function() {
    rejected_reason = $('.reason-text').val();

    selected_value = $(this).find(":checked").val();
    if (selected_value == 'reject'){
        $('.reason-text').css({
            'display':'block',
        });
    } else {
        $('.reason-text').css({
            'display':'none',
        });
    }
});

$(document).on("click", '.submit-product-return', function(e) {

   selected_value = $('#return_approval_status').find(":checked").val();
   rejected_reason = $('.reason-text-return').val();

   console.log(rejected_reason);

   var url = $(this).attr('data-url');
   var pk = $(this).attr('data-pk');

   acceptOrRejectReturn(selected_value,pk,rejected_reason,url);
});

$(".assign-delivery-agent-return").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('data-url');
    var return_pk = $(this).attr('data-return');
    var agent_pk = $('.delivery_agents_return').val();
    assignAgentForReturn(url,agent_pk,return_pk);
});

$("#onaiza-return-accept-button").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('data-url');
    var return_pk = $(this).attr('data-pk');

    receivedReturn(url,return_pk);
});


function assignAgentForReturn(url,pk,return_pk){
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            agent:pk,
            return_pk:return_pk,
        },
        success: function (data) {
            console.log(data);
            location.reload();
        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}

function assignAgent(url,pk,order){
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            agent:pk,
            order:order
        },
        success: function (data) {
            console.log(data);
            location.reload();
        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}

function acceptOrRejectReturn(returnStatus,pk,reason,url){
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
           pk:pk,
           status:returnStatus,
           rejected_reason:rejected_reason,
        },
        success: function (data) {
            console.log(data['status']);
            if(data['return_status']=='accepted'){
                  window.location.reload();

            } else {
                  window.location.reload();
            }
        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}

function receivedReturn(url,return_pk){
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {

           return_pk:return_pk,
        },
        success: function (data) {
            console.log(data['status']);
            window.location.reload();

        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}