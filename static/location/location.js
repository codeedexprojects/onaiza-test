
$("#id_name").change(function(){
        var name = $("#id_name").val();
        console.log(name);

        get_places(name);
});

function get_places(name){

    var url = $("#hidden-pincode").attr("data-url");

     $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            name:name
        },

        beforeSend: function() {
        console.log("Loading...............");
         $('.pincode-section-loader').css({
                'display':'block'
             });

              $('.pincode-section').css({
                'display':'none'
             });
        $('.pincode-section-loader p').text("Fetching Pincode Please Be Patient.......");
    },

        success: function (data) {
            console.log("+++++++++++++++");
            console.log(data);
            console.log("+++++++++++++++");
             $('.pincode-section-loader').css({
                'display':'none'
             });

              $('.pincode-section').css({
                'display':'block'
             });
            places = JSON.parse(data['values']);
            console.log(places);
            var options;
           for (var i = 0; i < places.length; i++) {
                options += "<option value="+places[i]['pincode'] +">"  + places[i]['name'] +'-'+ places[i]['pincode'] + "</option>";
                console.log(places[i]['name']);
            }

            $("#id_pincode").html(options);
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, data.toString(), "error");
            console.log(data)
        }
    });
}