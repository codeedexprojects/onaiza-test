
$('#id_banner_type').on('change', function() {
    selectedValue = $(this).find(":selected").val();

    if(selectedValue == "primary"){
        setPrimaryBanner();

    } else if(selectedValue == "secondary"){
        setSecondaryBanner();

    } else if(selectedValue == "tertiary"){
        setTertiaryBanner();

    }

    displayOfferType();
});

function setPrimaryBanner(){
     $('.banner-rep').css({
         "width": "100%",
     });
     $('.resolution-size').html("Full width banners");
}

function setSecondaryBanner(){
    $('.banner-rep').css({
            "width": "50%",
     });
    $('.resolution-size').html("Offer type banners etc");
}

function setTertiaryBanner(){
    $('.banner-rep').css({
        "width": "30%",
    });
    $('.resolution-size').html("Small type banners");
}

function displayOfferType(){
    $('.offer-type').attr('style', 'display: block !important');
}


$('#id_offer_type').on('change', function() {
    selectedValue = $(this).find(":selected").val();

    if(selectedValue == "product"){
      displayNoneExceptProduct();

    } else if(selectedValue == "category"){
       displayNoneExceptCategory();

    } else if(selectedValue == "brand"){
        displayNoneExceptBrand();
    }

   $('.offer-image').attr('style', 'display: block !important');
});

function displayNoneExceptProduct(){
    $('.brand-select').attr('style', 'display: none !important');
    $('.category-select').attr('style', 'display: none !important');
    $('.product-select').attr('style', 'display: block !important');
}

function displayNoneExceptCategory(){
    $('.brand-select').attr('style', 'display: none !important');
    $('.category-select').attr('style', 'display: block !important');
    $('.product-select').attr('style', 'display: none !important');
}

function displayNoneExceptBrand(){
    $('.brand-select').attr('style', 'display: block !important');
    $('.category-select').attr('style', 'display: none !important');
    $('.product-select').attr('style', 'display: none !important');
}