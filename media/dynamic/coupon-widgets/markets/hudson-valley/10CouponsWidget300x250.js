(function() {

// Localize jQuery variable
var jQuery;

/******** Load jQuery if not present *********/
if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.4.2') {
    var script_tag = document.createElement('script');
    script_tag.setAttribute("type","text/javascript");
    script_tag.setAttribute("src",
        "http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js");
    script_tag.onload = scriptLoadHandler;
    script_tag.onreadystatechange = function () { // Same thing but for IE
        if (this.readyState == 'complete' || this.readyState == 'loaded') {
            scriptLoadHandler();
        }
    };
    // Try to find the head, otherwise default to the documentElement
    (document.getElementsByTagName("head")[0] || document.documentElement).appendChild(script_tag);
} else {
    // The jQuery version on the window is the one we want to use
    jQuery = window.jQuery;
    main();
}

/******** Called once jQuery has loaded ******/
function scriptLoadHandler() {
    // Restore $ and window.jQuery to their previous values and store the
    // new jQuery in our local jQuery variable
    jQuery = window.jQuery.noConflict(true);
    // Call our main function
    main();
}

/******** Our main function ********/
function main() {
    jQuery(document).ready(function($) {

        /******* Load CSS *******/
        var css_reset_link = $("<link>", {
            rel: "stylesheet",
            type: "text/css",
            href: "http://local.10coupons.com/media/css/cleanslate.css"
        });
        var css_link = $("<link>", {
            rel: "stylesheet",
            type: "text/css",
            href: "http://local.10coupons.com/media/css/10CouponsWidgetmin011011.css"
        });
        css_reset_link.appendTo('head');
        css_link.appendTo('head');

        /******* Coupon Data *******/
        var data = {"site_name": "Hudson Valley", "site_name_no_spaces": "HudsonValley", "coupons": [], "site_url": "http://local.10coupons.com/hudson-valley/"}

		var container = '#coupon-container-med-rect';
		var wrapper = 'coupon-wrapper-med-rect';
		var set = 'med-rect';
		var buttons = 'Vert';

        $(container).addClass('cleanslate');

		$(container).html("<a href='" + data.site_url + "' class='coupon_logo' target='_parent'><div class='coupon_logo_name'>" + data.site_name_no_spaces + "</div></a>");
		// wrapper for coupon sets
		$(container).append("<div class='coupon_content_wrapper' id='" + wrapper + "'></div>");
		// small link at bottom
		$(container).append("<a href='" + data.site_url + "' class='bottom_link' target='_parent'>" + data.site_name + " Coupons</a>");

        num_coupons = data.coupons.length;
        if (num_coupons > 0){
            num_sets = Math.ceil(num_coupons/2);
        }else{
            num_sets = 1;
        }
        var k = 0;

        $(container).append("<div class='alt_content'><strong><a class='coupons-link' href='" + data.site_url + "' target='_parent'>WIN $10,000!</a></strong><span class='coupons-smalltext'> See <a class='coupons-link' href='" + data.site_url + "rules/'>rules</a> for details</span></div>")

		// create coupon sets, then unhide first set
		for (i=0; i < num_sets; i++){
			$('#' + wrapper).append("<div class='coupon_content coupons-hidden' id='coupon_" + set + "_" + [i+1] + "'></div>");
		}

        if (num_coupons > 0){
    		// add coupon data
    		for (i=0; i < num_sets; i++){
                $('#coupon_' + set + '_' + [i+1]).append("<a class='coupon_link' href='" + data.coupons[i+k].coupon_url + "' target='_parent'><span class='coupon_business_name'>" + data.coupons[i+k].business_name + "</span><span class='coupon_headline'>" + data.coupons[i+k].headline + "</span></a>");
                if ((i+k+1) < num_coupons){
                    $('#coupon_' + set + '_' + [i+1]).append("<a class='coupon_link' href='" + data.coupons[i+k+1].coupon_url + "' target='_parent'><span class='coupon_business_name'>" + data.coupons[i+k+1].business_name + "</span><span class='coupon_headline'>" + data.coupons[i+k+1].headline + "</span></a>");
                    k++;
                }
    		}
            $('#coupon_' + set + '_1').removeClass("coupons-hidden");
        }else{
            $('#' + wrapper).append("<div class='no_coupon_content' id='coupon_" + set + "_1'>Sign up to get 10 local coupons sent to your email inbox every week!<br/><br/><a class='coupons-btn' href='" + data.site_url + "' target='_parent'>Sign Up Now!</a></div>")
        }

		// scroll buttons
        if (num_coupons > 2){
    		$('#coupon_' + set + '_1').append("<div class='couponBtns" + buttons + "'><div class='couponBtnPrevOff' href='#'></div><div class='couponBtnNext' href='#'></div></div>");
    		for (i=2; i < num_sets; i++){
    			$('#coupon_' + set + '_' + [i]).append("<div class='couponBtns" + buttons + "'><div class='couponBtnPrev' href='#'></div><div class='couponBtnNext' href='#'></div></div>");
    		}
    		$('#coupon_' + set + '_' + num_sets).append("<div class='couponBtns" + buttons + "'><div class='couponBtnPrev' href='#'></div><div class='couponBtnNextOff' href='#'></div></div>");
    		$('.couponBtnPrev').click(function(){
    			var thisCouponSet = $(this).closest('.coupon_content');
    			$(thisCouponSet).addClass('coupons-hidden');
    			$(thisCouponSet).prev().removeClass('coupons-hidden');
    		});
    		$('.couponBtnNext').click(function(){
    			var thisCouponSet = $(this).closest('.coupon_content');
    			$(thisCouponSet).addClass('coupons-hidden');
    			$(thisCouponSet).next().removeClass('coupons-hidden');
    		});
        }
    });
}

})(); // Call our anonymous function immediately
