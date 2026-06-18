$(document).on("click", 'button[data-id="add-to-wishlist"]', function() {
    let is_login = $(this).hasClass("proceed_to_login")

    let id = $(this).attr("data-pk");
    var url = $(this).attr("href");
    $parent = $(this).parents('div[data-class="product"]');
//    var wishEmpty = $(this).('#wish-empty');
//    var wishFilled = $(this).('#wish-filled');

    let is_Notlogin = $(this).hasClass("proceed_to_login")
    console.log(is_Notlogin,"added to cart");
    if(is_Notlogin == true){
        $("#sign-ip").show();
        $("#SignIn").show();
    }else{

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
                console.log(data['status']);
              var imgAdded = $('span#'+id).find('img').attr("data-path");
              var imgEmpty = $('span#'+id).find('img').attr("data-path-empty");

              if(data['status']=='added'){
                    $('span#'+id).find('img').attr("src",imgAdded);


              } else if(data['status']=='null'){
                       document.getElementById("SignIn").style.display = "block";
                       document.getElementById("SignUp").style.display = "none";
                       $('#sign-ip').css({
                            'display':'flex'
                        });
              }  else if(data['status']=='not_in_batch'){
                       var title = "Not Available";
                        var message = "Product is not available in selected pincode";
                        swal(title, message, "error");
                        console.log(data);
              }

               else {
                   $('span#'+id).find('img').attr("src",imgEmpty);
              }

        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
            console.log(data)
        }
    });
}
});

$(document).on("click", '.add-to-cart', function() {
    let id = $(this).attr("data-pk");
    var url = $(this).attr("href");

    $parent = $(this).parents('div[data-class="product"]');

    let is_Notlogin = $(this).hasClass("proceed_to_login")

    console.log(id);
    console.log(url);

    console.log(is_Notlogin,"added to cart");

    if(is_Notlogin == true){
        $("#sign-ip").show();
        $("#SignIn").show();
    }else{
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
            console.log(data['status']);

            status = data['status'];

            if(status=='not_in_batch'){
                var title = "Product not available";
                var message = "Product is not available in your area!";
                swal(title, message, "error");

            } else if(data['status']=='different-location'){
                var title = "Different Location";
                var message = data["message"];
                swal(title, message, "error");

            } else if (status == 'added'){
                $('#single-product div.apply-cart').attr('style', 'display: none !important');
                $('#single-product div.my-cart').attr('style', 'display: block !important');

                //                      shows the quantity button
                $('#single-product .right-box .bottom div.quantity').attr('style', 'display: flex !important');
                $('input#theInput').val("1");

                //                    updating links to plus and minus buttons
                $('#single-product div.quantity input#minus').attr('data-pk', id);
                $('#single-product div.quantity input#plus').attr('data-pk', id);

                $('.bottom .quantity').addClass("flex");
                $('.bottom .apply').addClass("none");

                var pageURL = $(location).attr("href");
                console.log("The page url is an unex "+ pageURL);
                // $('#MyCart').load(pageURL + );
                $("#MyCart").load(location.href + " div#myCartChildren");
            }

        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
        }
    });
    }
});

//
//$(".add-to-cart").click(function(){
//    let id = $(this).attr("data-pk");
//    var url = $(this).attr("href");
//    $parent = $(this).parents('div[data-class="product"]');
//
//    console.log(id);
//    console.log(url);
//
//    $.ajax({
//        type: "GET",
//        url: url,
//        dataType: "json",
//        data: {
//            product_variant:id
//        },
//
//        success: function (data) {
//              console.log(data['status']);
//
//             $('.bottom .quantity').addClass("flex");
//             $('.bottom .apply').addClass("none");
//             var pageURL = $(location).attr("href");
//             console.log("The page url is an unex "+ pageURL);
////              $('#MyCart').load(pageURL + );
//              $("#MyCart").load(location.href + " div#myCartChildren");
//
//        },
//
//        error: function (data) {
//            var title = "An error occurred";
//            var message = "An error occurred. Please try again later.";
//            swal(title, message, "error");
//        }
//    });
//});


//cart incrememt
$(document).on("click", '.bottom .plus', function() {
    let id = $(this).attr("data-pk");
    var url = $(this).attr("href");

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
            $(`.${id} .input-text`).val(data['qty'])
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
        }
    });
});


//cart decrement
$(document).on("click", '.bottom .minus', function() {

    let id = $(this).attr("data-pk");
    var url = $(this).attr("href");

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
            $(`.${id} .input-text`).val(data['qty'])
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
        }
    });
});


// $('.minus-cart').click(function (e) {
$(document).on("click", '.minus-cart', function(e){
    e.preventDefault();
    var val = 0, $this = $(this);
    decrement_cart($this, val)
});

// $('.plus-cart').click(function (e) {
$(document).on("click", '.plus-cart', function(e){
    console.log("PLUSS++++++")
			e.preventDefault();
			var $this = $(this);
			var val = 0
		    increment_cart($this, val)
});

// $('.plus-checkout').click(function (e) {
$(document).on("click", '.plus-checkout', function(e){
			e.preventDefault();
			var $this = $(this);
			var val = 0
            increment_cart_checkout($this, val)
            // $(".amt1").load(location.href + " h6");
            // $(".amt1").load(location.href + " .total-amount");
});

// $('.minus-checkout').click(function (e) {
$(document).on("click", '.minus-checkout', function(e){
    e.preventDefault();
    var $this = $(this);
    var val = 0
    decrement_cart($this, val)
    // $(".amt").load(location.href + " .amt");
    // $(".amt1").load(location.href + " .amt1");
});


$("#customerAddress").on('click', 'li', function () {
    $("#customerAddress li.address-active").removeClass("address-active");
    $(this).addClass("address-active");
});


$('#proceed').click(function (e) {
    e.preventDefault();
    var element = $( "#customerAddress" ).find( "li.address-active" );
    var url = element.attr('data-url');
    var pk = element.attr('data-pk');
    set_adress_and_proceed(url,pk);
});


$('.removeCart').click(function (e) {
			e.preventDefault();
			var $this = $(this);
			var val = 0
            console.log("REMOVECART")
			remove_cart($this,"cart");
});

$('.remove-cart-checkout').click(function (e) {
			e.preventDefault();
			var $this = $(this);
			var val = 0
			remove_cart($this,"checkout");
});

$('#checkout').click(function (e) {
    e.preventDefault();
    var $this = $(this);
    proceedToPayment($this);
});

$('#cntn-shopping').click(function(){
    var redirectUrl = $(this).attr('data-url');
    var actionUrl = $(this).attr('data-action-url');
    clearCookiesAndContinueShopping(redirectUrl, actionUrl)
});

$(".productDetailsFooter .rightSide a ").click(function (e) {
    e.preventDefault();
    var pk = $(this).attr('data-pk');
    $('.'+pk).show();
});

$(".productDetailsFooter .leftSide a ").click(function (e) {
    e.preventDefault();
    var pk = $(this).attr('data-pk');
    $('.'+pk+'review').show();
});

$(".cancelButton-Row a button").click(function (e) {
    e.preventDefault();
    var pk = $(this).attr('data-pk');
    $('.'+pk).show();
});


$(".pincode-submit").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('data-url');
    var value = $('#pincodeSelect').val()
     setPincode(url, value);
});


$(document).on("click", '.bookNowButton', function(e) {
    e.preventDefault();

    var url = $(this).attr('data-url');
    var product_pk = $(this).attr('data-pk');

    console.log(url + product_pk);
    console.log("working");
    swal({
        title: "Are you sure?",
        // text: "Your will not be able to recover this imaginary file!",
        type: "warning",
        showCancelButton: true,
        confirmButtonClass: "btn-danger",
        confirmButtonText: "Yes!",
        confirmButtonColor: '#8CD4F5',
        closeOnConfirm: false
      },
      function(){
        swal("Booked!", "Successfully", "success");
        bookProduct(url, product_pk);
      });

});

// $(".add-to-cart-button").click(function (e)
$(document).on("click", '.add-to-cart-button', function(e   ){
    e.preventDefault();
    var url = $(this).attr('href');
    var product_pk = $(this).attr('data-pk');

    let is_no_pincode = $(this).hasClass("select-your-pincode")
    console.log(is_no_pincode,url + product_pk);
    let is_Notlogin = $(this).hasClass("proceed_to_login")
    if(is_Notlogin == true){
        $("#sign-ip").show();
        $("#SignIn").show();
    }else{
        if(is_no_pincode == true){
            // document.getElementById("SelectPincode").style.display = "block";
            $('.myPiccodePopup').click()
        }else{

            addToCart(url,product_pk,$(this))
        }

    }

});

$("#cancelOrderButton").click(function (e) {
    e.preventDefault();
    var url = $(this).attr('href');
    var order_pk = $(this).attr('data-pk');
});

//procedd to payment from time slot
$('#checkOutproduct button').click(function(){
    $('.tab3').removeClass('active')
    $('.tab2').addClass('active')

    $("#payment #checkOutproduct").hide();
    $("#payment .tab-click").slideDown("slow", function () {});
    $("#payment .tab-click").show();
});


$('.voucher-apply-button').click(function(e){
    e.preventDefault();
    var pk = $(this).attr('data-pk');
    var url = $(this).attr('data-url');

    var button = $(this)

    apply_coupon(pk,url,button);
});


$(".productVariant123").change(function(){
    var dop = $('.productVariant123').val();
    url = $("."+dop).attr('data-url');

    $(".content").load(url + " .content");
    $(".changable").load(url + " .changable");
    $("#single-product .right-box .top .right-card").load(url + " #single-product .right-box .top .right-card");

    // $(".right-box .content").load(url + " .right-box .bottom");
});


$(document).on("click", '.custom-select', function() {
    let value = $(".custom-select select").val();

    new_url = $("."+value).attr('data-goto');
    location.assign(new_url)

    // let url = $("."+value).attr('data-url');
    // update_product_variant(url, value);
});


$(document).on("click", '.ticket-submit', function(e) {
   e.preventDefault();
   url = $(this).attr('data-url');
   value = $("#description").val();

   newIssue(url,value);
});

$(document).on("click", '.apply-wallet-button', function(e) {
    e.preventDefault();
    url = $(this).attr('data-url');
    var input_field = $('.input-amount input').css('display')
    var point = $('.input-amount input').val()

    $('.input-amount input').css('display','block')

    if (input_field == 'block'){
        applyWalletAmount(url,this,point);
    }
});


$("#datepicker").on("change",function(){
    var date = $(this).val();
    url = $(this).attr('data-url')
    getTimeSlots(date,url);
});


$(document).on("click", '#checkOutproduct .container-side .checkOutContainer .timeSelect .timeInput', function() {
    $(this).addClass("active").siblings().removeClass('active');

    // getting the time slot pk and proceed to payment
    var time_slot_pk = $(this).attr('data-time-pk');
    $('#timeslot').val(time_slot_pk);
});


$(document).on("click", '.rating-product-submit', function(e) {
   e.preventDefault();
   url = $(this).attr('data-url');
   orderId = $(this).attr('data-order-id');

   $parent = $(this).parents('#ProductRating');

   review = $parent.find('.product-review').val();

   postRating(url,orderId,review);
});

$(document).on("click", '.search-button', function(e) {
   e.preventDefault();
   url = $(this).attr('data-url');

   $parent = $(this).parents('#spotlight');

   query = $('.search-query').val();

   location.href = url+"?query="+query;
});

$(document).on("click", '.cancel-order-popup', function(e) {
   e.preventDefault();

    console.log("Jiioo");
    var pk = $(this).attr('data-pk');
    var url = $(this).attr('data-url');

    getProductDetails(url,pk);
});

$('#cancelreason').change(function() {
    rejected_reason = $('#cancel-review').val();

    selected_value = $(this).find(":checked").val();
    console.log(selected_value);
    if (selected_value == 'others'){
        $('.SideTextareaMainContainer').css({
            'display':'block',
        });
        console.log("blocked")
    } else {
        $('.SideTextareaMainContainer').css({
            'display':'none',
        });
    }
});

$(document).on("click", '.return-product-button', function(e) {
   e.preventDefault();

    var pk = $(this).attr('data-pk');
    var url = $(this).attr('data-url');

    returnProduct(url,pk);
});

$(document).on("click", '.cancel-order-buttton', function(e) {
   e.preventDefault();

    var pk = $(this).attr('data-pk');
    var url = $(this).attr('data-url');

    cancelOrder(url,pk);
});

//functions starts

function decrement_cart($selector, val) {
    var parent = $selector.parents('.cart-items');
    var id = parent.find('.nameArea-Left').attr('data-pk');
    var url = parent.find('.nameArea-Left').attr('href');

   $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
              console.log(data['status']);
                parent.find('.input-text').val(data['qty']);
                if(data['qty'] == 0){
                    parent.remove();
                }

//                 updating cart overlay
                 $("#MyCart .price-details-MainContainer").load(location.href + " .price-details-MainContainer");
                 var total = data['total'];
                $('.total-amount').html(total)
                $('.item-total').html(total)

//             location.reload();
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
        }
    });
}

function increment_cart($selector, val) {
    var parent = $selector.parents('.cart-items');
    var id = parent.find('.plus-cart').attr('data-pk');
    var url = parent.find('.plus-cart').attr('href');

   $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
              console.log(data['status']);
                 parent.find('.input-text').val(data['qty']);
//             location.reload();
//                 updating cart overlay
             $("#MyCart .price-details-MainContainer").load(location.href + " .price-details-MainContainer");

        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";

        }
    });
}

function increment_cart_checkout($selector, val) {
    var parent = $selector.parents('.cart-items');
    var id = parent.find('.plus-checkout').attr('data-pk');
    var url = parent.find('.plus-checkout').attr('href');

   $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:id
        },

        success: function (data) {
              console.log(data['status']);
                parent.find('.input-text').val(data['qty']);
                $('.qty').val(data['qty'])
                console.log(data['total'])
                var total = data['total'];
                $('.total-amount').html(total)
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";

        }
    });
}

function set_adress_and_proceed(url,pk){

     $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            address:pk
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status'];

              if(status == 'true'){
                $('#payment .heading li').removeClass('active')
                $('.tab3').addClass('active')

//                $("#payment .tab-click").show();
                $("#address").hide();
//                $("#payment .tab-click").slideDown("slow", function () {});
                $("#payment #checkOutproduct").slideDown("slow", function () {});

              } else {
                $('#addressError').css({'display': 'block'});
              }
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";

        }
    });

}

function remove_cart($selector,section) {
    var parent = $selector.parents('.cart-items');
    var id;
    var url;

    if(section=='cart'){
        id = parent.find('.removeCart').attr('data-pk');
         url = parent.find('.removeCart').attr('data-url');
    } else if (section=='checkout'){
         id = parent.find('.remove-cart-checkout').attr('data-pk');
         url = parent.find('.remove-cart-checkout').attr('href');
    }

    console.log(section);
   $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            pk:id
        },

        success: function (data) {

              var result = data['status'];
              var total = data['total'];
              if(result=='true'){
                console.log(result);
                parent.css({"display":"none"});
                if(section=='cart'){
                    $(".price-details-data").load(location.href + " .price-details-data");

                } else if (section=='checkout'){
                     $(".amt1").load(location.href + " .amt1");

                }

              }

        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            console.log(message)
            console.log(data)
        }
    });
}

function proceedToPayment($selector) {

    var parent = $selector.parents('.tab-click'),method, number;

    var url = parent.find('#checkout').attr('data-url');
    var redirect_url = parent.find('#checkout').attr('data-redirect');
    var time_slot = $('#timeslot').val()
    var delivery_date = $('#datepicker').val()

    if($("input[type=text][name=upi]").val()){
        method = "upi";
        number = $("input[type=text][name=upi]").val()

    } else if($("input[type=text][name=creditCard]").val()) {
        method = "creditCard";
        number = $("input[type=text][name=creditCard]").val()

    } else if($("input[type=text][name=debitCard]").val()) {
        method = "debitCard";
        number = $("input[type=text][name=debitCard]").val()

    } else if($("input[type=text][name=gpay]").val()) {
        method = "gpay";
        number = $("input[type=text][name=gpay]").val()

    } else if($("input[type=text][name=apay]").val()) {
        method = "applePay";
        number = $("input[type=text][name=apay]").val()

    } else {
        method = "CashOnDelivery";
        method = "cod";
        number = ""
    }

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            method:method,
            number:number,
            time_slot:time_slot,
            delivery_date:delivery_date,
        },
        success: function (data) {
            let status = data["status"]

            if (status == "true"){
                let pk = data['pk']
                console.log(pk);
                window.location.replace(redirect_url+"?order="+pk);
            }else if (status == "different-location"){
                let title = "Not Available";
                let message = data["message"];
                swal(title, message, "error");
            }else if(status == "stock-unavailable"){
                let title = "Not Available";
                let stock_data = data["data"];
                let message = "";
                for (i=0; i<stock_data.length; i++){
                    let item = stock_data[i];
                    message += `${item["name"]} has only ${item["stock"]} in stock`;
                    if (i+1 == stock_data.length)
                        message += "\n"
                }

                swal(title, message, "error");
            }
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            console.log(message)
            console.log(data)
        }
    });
}

function setPincode(url,value){

     $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            pincode:value
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status'];

              if(status == 'true'){
                   $('#id01').css({"display":"none"});
                   window.location.reload();
              } else {

              }
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";

        }
    });

}

function bookProduct(url,product_pk){

     $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product:product_pk
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status'];

              if(status == 'true'){
                $(".bookNowButton").html('Booked !');
              } else {

              }
        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
        }
    });

}

function addToCart(url,product,$this){

    var image = $this.attr('data-image')

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            product_variant:product
        },

        success: function (data) {
            console.log(data['status']);
            if(data['status']=='null'){
                document.getElementById("SignIn").style.display = "block";
                $('#sign-ip').css({
                    'display':'flex'
                });

            } else if(data['status']=='not_in_batch'){
                var title = "Not Available";
                var message = "Product is not available in selected pincode";
                swal(title, message, "error");
            } else if(data['status']=='different-location'){
                var title = "Not Available";
                var message = data["message"];
                swal(title, message, "error");
            } else{
                $this.find('img').attr('src',image);
                var pageURL = $(location).attr("href");

                console.log("The page url is an unex "+ pageURL);
                // $('#MyCart').load(pageURL + );
                $("#MyCart").load(location.href + " div#myCartChildren");

              }

        },

        error: function (data) {
            var title = "An error occurred";
            var message = "An error occurred. Please try again later.";
            swal(title, message, "error");
        }
    });
}

function apply_coupon(pk,url,button){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            pk:pk
        },

        success: function (data) {
              console.log(data['status']);
              if(data['status']=='true'){
                    var amt = data['total_amt']
                    var percent_amt = data['percent_amt']

                    $('.coupon-amt').html(percent_amt);
                     $('.total-amt .total-td').html(data['total_amt']);


                    $(".voucher-apply-button").text("Apply");
                    $(button).text("Applied");
                    $(".voucher-apply-button").removeClass("applied");
                    $(button).addClass("applied");

              } else if (data['status']=='false'){
                    var title = "An error occurred";
                    var message = "Your are not eligible for this coupon";
                    swal(title, message, "error");
              }else {
                    var title = "An error occurred";
                    var message = "An Error Occoured";
                    swal(title, message, "error");
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

function update_product_variant(url,value){
    console.log(url);

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            pk:value
        },

        success: function (data) {
              console.log(data);
              if(data['status']=='true'){
                var is_cart = data['cart'];
                cart_qty = data['cart_qty']
                product_pk = data['pk'];
                is_wishlist =  data['is_wishlist'];
                let image = data['image'];
                stock = data['stock'];

                console.log(stock);

                var wishEmpty = $(".right-card span.wishlist button img").attr("data-path-empty");
                var wishFilled = $(".right-card span.wishlist button img").attr("data-path");

                $(".right-card span.wishlist button").attr('data-pk',product_pk);
                $(".right-card span.wishlist").attr('id',product_pk);
                $('.product-name').html(data['name']);
                $('.product-mrp').html("₹" + data['retail_price'] + " /-");
                $('.product-cross-mrp').html("₹" + data['mrp'] + " /-");
                $(".variant-image img").attr('src',"/media/"+data['image']);

                //  if product exists in cart
                if(is_cart=="True"){
                    $('#single-product div.apply-cart').attr('style', 'display: none !important');
                    $('#single-product div.book-now-button').attr('style', 'display: none !important');

                    //  shows the quantity button
                    $('#single-product .right-box .bottom div.quantity').attr('style', 'display: flex !important');
                    $('#single-product input#theInput').val(cart_qty);

                    $(".apply.my-cart").addClass("block");
                    $(".apply.my-cart").removeClass("none");

                    //  updating links to plus and minus buttons
                    $('#single-product div.quantity input#minus').attr('data-pk', product_pk);
                    $('#single-product div.quantity input#plus').attr('data-pk', product_pk);

                } else {

                   if(stock=="0"){
                        $('#single-product div.apply-cart').attr('style', 'display: none !important');
                        $('#single-product div.book-now-button').attr('style', 'display: flex !important');
                    } else {
                       $('#single-product div.apply-cart').attr('style', 'display: block !important');
                        $('#single-product div.book-now-button').attr('style', 'display: none !important');
                    }
                    $(".apply.my-cart").removeClass("block")
                    $(".apply.my-cart").addClass("none")

                    //   hides the quantity button
                   $('#single-product .right-box .bottom div.quantity').attr('style', 'display: none !important');

//                   new cart button
                    $('#single-product div.apply-cart button').attr('data-pk',product_pk);

//                   plus and minus button update pk
                    $('#single-product div.quantity input#minus').attr('data-pk', product_pk);
                    $('#single-product div.quantity input#plus').attr('data-pk', product_pk);
                }
                if (image){
                    $('#single-product .left-box .left-box-single-pic img').attr('src', image)
                }

                if(is_wishlist=="True"){
                    $(".right-card span.wishlist button img").attr('src',wishFilled);
                } else {
                    $(".right-card span.wishlist button img").attr('src',wishEmpty);
                }

              } else {}
        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}

function newIssue(url,value){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            description:value
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status']

              if(status=='true'){
                 var title = "Submitted Successfully";
                var message = "Ticket Submitted Successfully";
                swal(title, message, "success");
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

function applyWalletAmount(url,button,point){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            point:point,
        },
        success: function (data) {
              console.log(data['status']);
              status = data['status']

              $('.wallet-error-text').attr('style','display: none !important');

              console.log(data);

              if(data['state']=='exceed'){
              console.log("inside if conditon")
                $('.wallet-error-text').attr('style','display: block !important');
              }

              if(status=='true'){
                $('.total-amt .total-td').html(data['total']);
                // $(button).addClass("applied");
                $('#wallet-amount').html(data['value']);
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

function getTimeSlots(date){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            date:date
        },

        success: function (data) {

                var slots , json_slots;

              slots = data['slots']
              console.log(slots);
            //   json_slots = JSON.parse(slots)

              $(".timeSelect").empty();


            // if (json_slots.length == 0){
            if (slots.length == 0){
                $("#not_slots_available").show()
            }
            else{
                $("#not_slots_available").hide()
                for (var i = 0; i < slots.length; i++) {
                    console.log(slots[i]['name']);

                    $(".timeSelect").append(
                        `<div class="timeInput" data-time-pk="${slots[i]['pk']}">
                            <h6>${slots[i]['name']}</h6>
                            <input name="fav_language" type="radio" value="">
                        </div>`
                    );
               }
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

function clearCookiesAndContinueShopping(redirectUrl, actionUrl){
    console.log(actionUrl);

    $.ajax({
        type: "GET",
        url: actionUrl,
        dataType: "json",
        data: {

        },
        success: function (data) {
            console.log(data);
            window.location.replace(redirectUrl);
        },

        error: function (data) {
            var title = "An error occurred";
            var message = data;
            console.log(data);
            swal(title, message, "error");
        }
    });
}

function postRating(url,orderId,review){

    rating = $("input[name='rating']:checked").val();
    console.log("===>>>"+review);

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            rating : rating,
            review : review,
            order_id : orderId,
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status']

              if(status=='true'){
                 var title = "Rated Successfully";
                var message = "Ratings Submitted Successfully";
                swal(title, message, "success");
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

function search(url,query){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            query: query,
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status']

              if(status=='true'){
                 var title = "Rated Successfully";
                var message = "Ratings Submitted Successfully";
                swal(title, message, "success");
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

function getProductDetails(url,order_item_pk){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            order_item_pk: order_item_pk,
        },

        success: function (data) {
              console.log(data['product_name']);
              status = data['status']

              if(status=='true'){
                   $('.product_name').text(data['product_name']);
                    $('.product_category').text(data['product_category']);
                   $('.product-mrp').text(data['product_mrp']);
                   $('.product-image').attr("src", data['product_image']);
                   $('.return-product-button').attr("data-pk",data['order_item_pk'] );

                  $('#CancelOrder').css({
                    'display':'block',
                });
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

function returnProduct(url,order_item_pk){

    cancel_reason = $('#cancelreason').find(":checked").val();
    cancel_review = $('#cancel-review').val();

    console.log("return aajax")

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            order_item_pk: order_item_pk,
            cancel_reason:cancel_reason,
            cancel_review:cancel_review,
        },

        success: function (data) {
              console.log(data['status']);
              status = data['status']

              if(status=='accepted'){
                    var title = "Return Submitted";
                    var message = "Product return successfully submitted";
                    console.log(data);
                    swal(title, message, "success");
             } else {
                var title = "Period is over";
                var message = "Return time period is over";
                console.log(data);
                swal(title, message, "error");
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

function cancelOrder(url,order_pk){

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        data: {
            order_pk: order_pk,

        },

        success: function (data) {
               console.log("status==========??")
              console.log(data['status']);
              status = data['status']

             if(data['status']=="cancelled"){

                 var title = "Order Cancelled";
                var message = "Order Cancelled";
                swal(title, message, "success");

             } else {
                 var title = "Period was over";
                var message = "Order Cancellation period was over";
                swal(title, message, "error");
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
