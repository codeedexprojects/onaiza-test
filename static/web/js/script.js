$(document).on("resize", function () {
	MySlick();
});

$(document).ready(function () {
	$("header .menu").click(function () {
		console.log("555");
		$("header .mobile-view").slideDown("slow", function () {
			$("header .menu").hide();
			$("header .close").show();
		});
	});

	$("header .close").click(function () {
		$("header .mobile-view").slideUp("slow", function () {
			$("header .close").hide();
			$("header .menu").show();
		});
	});

	function equalcard(s) {
		var h = 0;
		var line_height = 0;
		$(s).css("height", "auto");
		$(s).each(function () {
			var height = $(this).outerHeight(true);
			if (height > h) {
				h = height;
			}
		});
		$(s).height(h);
	}
	equalcard("#shops-home-page .content-box .shop-name-box h4");

	$(".wrapper .category-sub .head h3").click(function () {
		$(".wrapper .category-sub .dropdown-nav").toggle();
	});

	$(".wrapper .category-sub .dropdown-nav .icon button").click(function () {
		$(this).parent().find("ul.drop").toggle();
	});

	// edit-profile
	$(".side-popup-close").click(function () {
		console.log("99999");
		$("#EditProfile").show();
	});
	$(".SubButtonArea-EditProfile button").click(function () {
		console.log("99999");
		$("#EditProfile").show();
	});

	// tab
	$("#review-list .tab1").click(function () {
		$("#review-list .tab .common").removeClass("active");
		$(this).addClass("active");
		$("#review-list .describtion").show();
		$("#review-list .reviews").hide();
		$("#review-list .describtion").slideDown("slow", function () {});
	});

	$("#review-list .tab2").click(function () {
		$("#review-list .tab .common").removeClass("active");
		$(this).addClass("active");
		$("#review-list .reviews").show();
		$("#review-list .describtion").hide();
		$("#review-list .reviews").slideDown("slow", function () {});
	});

	$("#profileSinglePage .rightprofile a").click(function () {
		$("#EditProfile.OverLay").show();
	});

	$("#payment .heading li.tab1").click(function () {
		$("#payment .heading li").removeClass("active");
		$(this).addClass("active");
		$("#address").show();
		$("#payment .tab-click").hide();
		$("#address").slideDown("slow", function () {});
	});

	$("#payment .heading li.tab2").click(function () {
		$("#payment .heading li").removeClass("active");
		$(this).addClass("active");
		$("#payment .tab-click").show();
		$("#address").hide();
		$("#payment .tab-click").slideDown("slow", function () {});
	});

	// add-address
	$("#address div.bottom div.header-box div.right a.add-button").click(
		function () {
			$("#AddNewAddress").show();
		}
	);
	$(".side-popup-close").click(function () {
		$("#AddNewAddress").hide();
		$("#popupBackground").hide();
	});
	// edit-address
	//$(".AddressMainContainer .buttonAreaSub button").click(function () {
	//	$("#EditAddress").show();
	//	$("#AddNewAddress").hide();
	//})
	$(".side-popup-close").click(function () {
		$("#EditAddress").hide();
	});
	// my-cart
	$(".my-cart").click(function () {
		$("#MyCart").show();
	});
	$(".side-popup-close").click(function () {
		$("#MyCart").hide();
	});
	// popup-close
	$("#sign-ip").hide();
	$(".SignSub-Container .close-icon").click(function () {
		$("#sign-ip").hide();
	});
	// popup-sign-up
	//$(".SignSub-Container .sign-in-open").click(function () {
	//	$("#SignUp").show();
	//	$("#SignIn").hide();
	//})
	// popup-otp-verification
	//$(".SignSub-Container .next-otp").click(function () {
	//	$("#OTP").show();
	//	$("#SignIn").hide();
	//})
	// popup-otp-success
	//$(".SignSub-Container .next-success").click(function () {
	//	$("#OTPSuccess").show();
	//	$("#OTP").hide();
	//})

	// logout popup
	$("header .right .logoutPopup").click(function () {
		$("#sign-ip").hide();
		$("#SignUp").hide();
		$("#SignIn").show();
	});

	// procuct rating
	//$("#ProductRating.OverLay").hide();
	//$(".productDetailsFooter .leftSide a ").click(function () {
	//	$("#ProductRating").show();
	//})
	//   orderStatus
	//$(".productDetailsFooter .rightSide a ").click(function () {
	//	$("#SingleOrder.OverLay").show();
	//})
	// tickets
	// $("#Tickets .tab button").click(function () {
	// 	$(this).addClass('active').siblings().removeClass('active');
	// })
	// $("#Tickets .tab tablink1").click(function () {
	// 	$("#new.tabcontent").show();
	// 	$("#active.tabcontent").hide();
	// 	$("#resolved.tabcontent").hide();
	// })

	// nav-active
	$("header div.left nav ul li").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	$("#web .container .cards .card").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});
	$("#payment .left .item").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	//   orderconfirmed
	//  $('.main-container .product-details-main-container .product-details-Subrow').on('click', function(){
	// 	$("#SingleOrder.OverLay").show();
	//   });
	//  $('.orderTrackingMain-Container .orderTrackingSub-Container .cancelButton-Row a button').on('click', function(){
	//	$("#SingleOrder.OverLay").hide();
	//	$("#CancelOrder.OverLay").show();
	//  });

	// ticket radio button
	$("#Tickets .radioSection .container ").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	// overlay common background
	$(".myTicketPopup").on("click", function () {
		$("#popupBackground").show();
	});
	$("#Tickets .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".my-cart").on("click", function () {
		$("#popupBackground").show();
	});
	$("#MyCart .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".profileDetailsMainRow .rightprofile a").on("click", function () {
		$("#popupBackground").show();
	});
	$("#EditProfile .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".productDetailsFooter a").on("click", function () {
		$("#popupBackground").show();
	});
	$("#ProductRating .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});
	$("#CancelOrder .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#address div.bottom div.header-box div.right a.add-button").on("click", function () {
		$("#popupBackground").show();
	});

	$("#AddNewAddress .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#EditAddress .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#Tickets.OverLay").hide();
	$(".myTicketPopup").on("click", function () {
		$("#Tickets.OverLay").show();
	});

	// PiccodePopup
	$(".myPiccodePopup").on("click", function () {
		$("#id01").show();
	});

	// popup-sign-in
	//$(".SignSub-Container .next-sign-in").click(function () {
	//	$("#SignIn").show();
	//	$("#SignUp").hide();
	//})
	// cancel-order
	$(".side-popup-close").click(function () {
		$(".OverLay").hide();
	});

	$(".SignSub-Container .sign-up-open").click(function () {
		$("#SignIn").show();
		$("#SignUp").hide();
		var message = $(".sign-up-message");
		message.empty();
	});

	$(".SignSub-Container .sign-in-open").click(function () {
		$("#SignUp").show();
		$("#SignIn").hide();
		var message = $(".sign-up-message");
		message.empty();
	});

	// popup-sign-up
	//$(".SignSub-Container .sign-in-open").click(function () {
	//	$("#SignUp").show();
	//	$("#SignIn").hide();
	//})
	// popup-otp-verification
	//$(".SignSub-Container .next-otp").click(function () {
	//	$("#OTP").show();
	//	$("#SignIn").hide();
	//})
	// popup-otp-success
	//$(".SignSub-Container .next-success").click(function () {
	//	$("#OTPSuccess").show();
	//	$("#OTP").hide();
	//})

	// logout popup
	$("header .right .logoutPopup").click(function () {
		$("#sign-ip").show();
		// $("#SignUp").show();
		$("#SignUp").hide();
		$("#SignIn").show();
	});
	// procuct rating
	//$("#ProductRating.OverLay").hide();
	//$(".productDetailsFooter .leftSide a ").click(function () {
	//	$("#ProductRating").show();
	//})
	//   orderStatus
	//$(".productDetailsFooter .rightSide a ").click(function () {
	//	$("#SingleOrder.OverLay").show();
	//})
	// tickets
	// $("#Tickets .tab button").click(function () {
	// 	$(this).addClass('active').siblings().removeClass('active');
	// })
	// $("#Tickets .tab tablink1").click(function () {
	// 	$("#new.tabcontent").show();
	// 	$("#active.tabcontent").hide();
	// 	$("#resolved.tabcontent").hide();
	// })

	// nav-active
	$("header div.left nav ul li").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	$("#web .container .cards .card").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});
	$("#payment .left .item").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	//   orderconfirmed
	//  $('.main-container .product-details-main-container .product-details-Subrow').on('click', function(){
	// 	$("#SingleOrder.OverLay").show();
	//   });
	//  $('.orderTrackingMain-Container .orderTrackingSub-Container .cancelButton-Row a button').on('click', function(){
	//	$("#SingleOrder.OverLay").hide();
	//	$("#CancelOrder.OverLay").show();
	//  });

	// ticket radio button
	$("#Tickets .radioSection .container ").on("click", function () {
		$(this).addClass("active").siblings().removeClass("active");
	});

	// overlay common background
	$(".myTicketPopup").on("click", function () {
		$("#popupBackground").show();
	});
	$("#Tickets .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".my-cart").on("click", function () {
		$("#popupBackground").show();
	});
	$("#MyCart .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".profileDetailsMainRow .rightprofile a").on("click", function () {
		$("#popupBackground").show();
	});
	$("#EditProfile .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$(".productDetailsFooter a").on("click", function () {
		$("#popupBackground").show();
	});
	$("#ProductRating .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});
	$("#CancelOrder .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#address div.bottom div.header-box div.right a.add-button").on("click",function () {
		$("#popupBackground").show();
	});

	$("#AddNewAddress .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#address div.bottom div.container div.item div.two div.option a.edit").on("click", function () {
		$("#popupBackground").show();
		$("#EditAddress.OverLay").show();
        let action = $(this).attr('data-post_url');
        let url = $(this).attr('data-get_url');

        $.ajax({
            type: "GET",
            url: url,
            dataType: 'json',
            data: {},
            success: function (data) {
                var html_content = data['html_content'];
                $('#EditAddress.OverLay form').html(html_content);
                $('#EditAddress.OverLay form').attr('action', action);
            },
            error: function (data) {
				$("#popupBackground").hide();
				$("#EditAddress.OverLay").hide();
            }
		});

	});

	$("#EditAddress .side-popup-close ").on("click", function () {
		$("#popupBackground").hide();
	});

	$("#Tickets.OverLay").hide();
	$(".myTicketPopup").on("click", function () {
		$("#Tickets.OverLay").show();
	});

	// PiccodePopup
	$(".myPiccodePopup").on("click", function () {
		$("#id01").show();
	});

	// support
	$("header .supportPopup").on("click", function () {
		$("#id02").show();
	});
	$(
		".w3-container #id02.w3-modal .background .w3-modal-content .side-popup-close"
	).on("click", function () {
		$("#id02").hide();
	});

	// editadress

	$(
		"#checkOutproduct .container-side .checkOutContainer .timeSelect .timeInput "
	).click(function () {
		$(this).addClass("active").siblings().removeClass("active");

		//    getting the time slot pk and proceed to payment
		var time_slot_pk = $(this).attr("data-time-pk");
		$("#timeslot").val(time_slot_pk);
	});

	//   slider
	var length = $("#slick-slider .card").length;
	var width = $(document).width();

	function FirstSlider() {
		console.log("first slider");
		if (
			(width > 981 && length > 6) ||
			(width > 796 && width <= 980 && length > 4) ||
			(width <= 796 && length > 2)
		) {
			$("#slick-slider").slick({
				autoplay: true,
				autoplaySpeed: 3000,
				arrows: false,
				// prevArrow: $("#firstSlider .left-arrow"),
				// nextArrow: $("firstSlider .next-arrow"),
				draggable: true,
				infinite: true,
				pauseOnHover: false,
				slidesToShow: 6,
				slidesToScroll: 1,
				centerMode: true,
				infinite: true,
				dots: false,
				nav: true,

				responsive: [
					{
						breakpoint: 1300,
						settings: {
							slidesToShow: 6,
							infinite: true,
							centerPadding: "0px 80px",
						},
					},
					{
						breakpoint: 1100,
						settings: {
							slidesToShow: 5,
							infinite: true,
							centerPadding: "0px 80px",
						},
					},
					{
						breakpoint: 900,
						settings: {
							slidesToShow: 4,
							infinite: true,
							centerPadding: "0px 80px",
						},
					},
					{
						breakpoint: 700,
						settings: {
							slidesToShow: 3,
							infinite: true,
							centerPadding: "0px 80px",
						},
					},
					{
						breakpoint: 550,
						settings: {
							slidesToShow: 2,
							infinite: true,
							centerPadding: "0px 80px",
						},
					},
				],
			});
		}
	}
	FirstSlider();

	if ($("#firstSlider .slick-slide").length > 1) {
	}

	// previous next button css
	$("#firstSlider .slick-next").click(function () {
		$("#slick-slider").slick("slickNext");
	});
	$("#firstSlider .slick-prev").click(function () {
		$("#slick-slider").slick("slickPrev");
	});
	let len = $("#slick-slider-two .item").length

	if (len > 4) {
		$("#slick-slider-two").slick({
			autoplay: false,
			autoplaySpeed: 3000,
			arrows: false,
			draggable: true,
			infinite: true,
			pauseOnHover: false,
			slidesToShow: 4,
			slidesToScroll: 1,
			centerMode: false,
			infinite: true,
			dots: false,
			nav: true,
			responsive: [
				{
					breakpoint: 1300,
					settings: {
						slidesToShow: 4,
					},
				},
				{
					breakpoint: 1200,
					settings: {
						slidesToShow: 3,
					},
				},
				{
					breakpoint: 951,
					settings: {
						slidesToShow: 2,
					},
				},
				{
					breakpoint: 550,
					settings: {
						slidesToShow: 1,
					},
				},
			],
		});

		// previous next button css
		$("#grocery .slick-next").click(function () {
			$("#slick-slider-two").slick("slickNext");
		});
		$("#grocery .slick-prev").click(function () {
			$("#slick-slider-two").slick("slickPrev");
		});
	}

	var length = $("#slick-slider-offer .item").length;
	var width = $(document).width();

	function MySlick() {
		if (
			(width > 1280 && length > 3) ||
			(width > 640 && width <= 1280 && length > 2) ||
			(width > 320 && width <= 640 && length > 1)
		) {
			$("#slick-slider-offer").slick({
				autoplay: true,
				autoplaySpeed: 3000,
				arrows: false,
				draggable: true,
				infinite: true,
				pauseOnHover: false,
				slidesToShow: 3,
				slidesToScroll: 1,
				centerMode: false,
				infinite: true,
				dots: false,
				nav: true,
				responsive: [
					{
						breakpoint: 1280,
						settings: {
							slidesToShow: 2,
						},
					},
					{
						breakpoint: 600,
						settings: {
							slidesToShow: 1,
						},
					},
				],
			});
		}
	}
	MySlick();

	// previous next button css
	$("#grocery .slick-next").click(function () {
		$("#slick-slider-offer").slick("slickNext");
	});
	$("#grocery .slick-prev").click(function () {
		$("#slick-slider-offer").slick("slickPrev");
	});

	var length = $("#slick-slider-shop .item").length;
	var width = $(document).width();

	function MyFunction() {
		console.log("hey");
		if (
			(width > 320 && width <= 640 && length > 1) ||
			(width > 640 && width <= 1280 && length > 2) ||
			(width > 1280 && length > 3)
		) {
			console.log("if");
			$("#slick-slider-shop").slick({
				autoplay: true,
				autoplaySpeed: 3000,
				arrows: false,
				draggable: true,
				infinite: true,
				pauseOnHover: false,
				slidesToShow: 3,
				slidesToScroll: 1,
				centerMode: false,
				infinite: true,
				dots: false,
				nav: true,
				responsive: [
					{
						breakpoint: 981,
						settings: {
							slidesToShow: 2,
						},
					},
					{
						breakpoint: 700,
						settings: {
							slidesToShow: 1,
						},
					},
					{
						breakpoint: 480,
						settings: {
							slidesToShow: 1,
						},
					},
				],
			});
		}
	}
	MyFunction();

	var length = $("#slick-slider-product-single .image").length;
	var width = $(document).width();

	function MySlick() {
		if (length > 1) {
			$("#slick-slider-product-single").slick({
				autoplay: false,
				autoplaySpeed: 3000,
				arrows: false,
				draggable: true,
				infinite: true,
				pauseOnHover: false,
				slidesToShow: 3,
				slidesToScroll: 1,
				centerMode: false,
				infinite: true,
				dots: false,
				nav: true,
				vertical: true,
				asNavFor: "#slick-slider-product-singles",
				focusOnSelect: true,
			});
		}
	}
	MySlick();

	$("#slick-slider-product-singles").slick({
		autoplay: false,
		autoplaySpeed: 3000,
		arrows: false,
		draggable: true,
		infinite: true,
		pauseOnHover: false,
		slidesToShow: 1,
		slidesToScroll: 1,
		centerMode: false,
		infinite: true,
		dots: false,
		nav: true,
		vertical: false,
		asNavFor: "#slick-slider-product-single",
		focusOnSelect: false,
	});

	$("header .mobile").click(function () {
		$("header .mobile").hide();
		$("header .close").show();
		$(".menu-container").slideDown("slow", function () {});
	});

	$(
		"header .close, header .menu-container .menu ul li, header .head-main .menu-container .button"
	).click(function () {
		$("header .close").hide();
		$("header .mobile").show();
		$(".menu-container").slideUp("slow", function () {});
	});

	var wow = new WOW({
		boxClass: "wow",
		animateClass: "animated",
		offset: 0,
		mobile: true,
		live: true,
		callback: function (box) {},
		scrollContainer: null,
		resetAnimation: true,
	});
	wow.init();
});

$(window).scroll(function () {
	var scroll_pos = 0;

	scroll_pos = $(this).scrollTop();

	if (scroll_pos > 0) {
		$("#spotlight header").css("background-color", "#fef9f6");
		$("#spotlight header").css(
			"box-shadow",
			"rgb(68 68 68 / 5%) 2px 3px 3px"
		);
	} else if (scroll_pos == 0) {
		$("#spotlight header").removeAttr("style");
	}

	if ($(".card1").hasClass("active")) {
		$("card1.active")
			.children("img")
			.attr("src", "./images/icons/website active.png");
	}

	$(document).on("scroll", function () {});
});

// My ticket

// function TicketsOff() {
// 	document.getElementById("Tickets").style.display = "none";
// }
function itemReviews(evt, cityName) {
	var i, tabcontent, tablinks;
	tabcontent = document.getElementsByClassName("tabcontent");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].style.display = "none";
	}
	tablinks = document.getElementsByClassName("tablinks");
	for (i = 0; i < tablinks.length; i++) {
		tablinks[i].className = tablinks[i].className.replace(" active", "");
	}
	document.getElementById(cityName).style.display = "block";
	evt.currentTarget.className += " active";
}

var x, i, j, l, ll, selElmnt, a, b, c;
x = document.getElementsByClassName("custom-select");
l = x.length;
for (i = 0; i < l; i++) {
	selElmnt = x[i].getElementsByTagName("select")[0];
	ll = selElmnt.length;
	a = document.createElement("DIV");
	a.setAttribute("class", "select-selected");
	a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
	x[i].appendChild(a);
	b = document.createElement("DIV");
	b.setAttribute("class", "select-items select-hide");
	for (j = 1; j < ll; j++) {
		c = document.createElement("DIV");
		c.innerHTML = selElmnt.options[j].innerHTML;
		c.addEventListener("click", function (e) {
			var y, i, k, s, h, sl, yl;
			s = this.parentNode.parentNode.getElementsByTagName("select")[0];
			sl = s.length;
			h = this.parentNode.previousSibling;
			for (i = 0; i < sl; i++) {
				if (s.options[i].innerHTML == this.innerHTML) {
					s.selectedIndex = i;
					h.innerHTML = this.innerHTML;
					y =
						this.parentNode.getElementsByClassName(
							"same-as-selected"
						);
					yl = y.length;
					for (k = 0; k < yl; k++) {
						y[k].removeAttribute("class");
					}
					this.setAttribute("class", "same-as-selected");
					break;
				}
			}
			h.click();
		});
		b.appendChild(c);
	}
	x[i].appendChild(b);
	a.addEventListener("click", function (e) {
		e.stopPropagation();
		closeAllSelect(this);
		this.nextSibling.classList.toggle("select-hide");
		this.classList.toggle("select-arrow-active");
	});
}

function closeAllSelect(elmnt) {
	var x,
		y,
		i,
		xl,
		yl,
		arrNo = [];
	x = document.getElementsByClassName("select-items");
	y = document.getElementsByClassName("select-selected");
	xl = x.length;
	yl = y.length;
	for (i = 0; i < yl; i++) {
		if (elmnt == y[i]) {
			arrNo.push(i);
		} else {
			y[i].classList.remove("select-arrow-active");
		}
	}
	for (i = 0; i < xl; i++) {
		if (arrNo.indexOf(i)) {
			x[i].classList.add("select-hide");
		}
	}
}

document.addEventListener("click", closeAllSelect);

// custom select end

// header drop down

window.onclick = function (event) {
	if (!event.target.matches(".dropbtn")) {
		var dropdowns = document.getElementsByClassName("drop");
		var i;
		for (i = 0; i < dropdowns.length; i++) {
			var openDropdown = dropdowns[i];
			if (openDropdown.classList.contains("show")) {
				openDropdown.classList.remove("show");
			}
		}
	}
};

function snackBarFunction(message) {
	// Get the snackbar DIV
	var x = document.getElementById("snackbar");
	x.value = message;
	// Add the "show" class to DIV
	x.className = "show";

	// After 3 seconds, remove the show class from DIV
	setTimeout(function () {
		x.className = x.className.replace("show", "");
	}, 3000);
}

$(".snack-btn").click(function () {
	message = $(this).attr("data-message");
	$("#snackbar").html(message);
	snackBarFunction("Hellooooooo");
});
