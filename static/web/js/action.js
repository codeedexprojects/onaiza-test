$('#id_is_exclusive').change(function() {
       if(this.checked) {
        console.log("checked");
        $('#voucherCustomer').css({
            'display':'block'
        });
    }else{
        console.log("un-checked");
        $('#voucherCustomer').css({
            'display':'none'
        });
    }
});