head.ready("jquery", function(){

    $(".valid_days").hover(
        function(){$(".restrictions").removeClass("edit");},
        function(){$(".restrictions").addClass("edit");}
    );

    function check_valid_days() {
        var is_valid_monday = $("#id_is_valid_monday").is(":checked");
        var is_valid_tuesday = $("#id_is_valid_tuesday").is(":checked");
        var is_valid_wednesday = $("#id_is_valid_wednesday").is(":checked");
        var is_valid_thursday = $("#id_is_valid_thursday").is(":checked");
        var is_valid_friday = $("#id_is_valid_friday").is(":checked");
        var is_valid_saturday = $("#id_is_valid_saturday").is(":checked");
        var is_valid_sunday = $("#id_is_valid_sunday").is(":checked");
        var valid_days = '';
        var valid_days_count = 0;
        var valid_days_list = [is_valid_monday, is_valid_tuesday, is_valid_wednesday, is_valid_thursday, is_valid_friday, is_valid_saturday, is_valid_sunday];
        jQuery.each(valid_days_list, function() {
            if (this == true) {
                valid_days_count = valid_days_count + 1;
            }
        })
        //alert(valid_days_count);
        if (valid_days_count > 0) {
            valid_days = create_valid_days_string(valid_days_count, is_valid_monday, is_valid_tuesday, is_valid_wednesday, is_valid_thursday, is_valid_friday, is_valid_saturday, is_valid_sunday);
        }
        return valid_days;
    }

    function create_valid_days_string(valid_days_count, is_valid_monday, is_valid_tuesday, is_valid_wednesday, is_valid_thursday, is_valid_friday, is_valid_saturday, is_valid_sunday) {
        var valid_days_temp_count = valid_days_count;
        if (valid_days_count == 7) {
            valid_days_string = 'Offer good 7 days a week.';
        }
        else if (valid_days_count == 6){
            if (is_valid_sunday == false) {
                valid_days_string = 'Offer good Monday - Saturday only.';
            } else {
                valid_days_string = 'Offer not valid ';
                if (is_valid_monday == false) {
                    valid_days_string = valid_days_string + 'Mondays.';
                }
                if (is_valid_tuesday == false) {
                    valid_days_string = valid_days_string + 'Tuesdays.';
                }
                if (is_valid_wednesday == false) {
                    valid_days_string = valid_days_string + 'Wednesdays.';
                }
                if (is_valid_thursday == false) {
                    valid_days_string = valid_days_string + 'Thursdays.';
                }
                if (is_valid_friday == false) {
                    valid_days_string = valid_days_string + 'Fridays.';
                }
                if (is_valid_saturday == false) {
                    valid_days_string = valid_days_string + 'Saturdays.';
                }
            }
        }
        else if (valid_days_count == 5 && is_valid_saturday == false && is_valid_sunday == false) {
           valid_days_string = 'Offer good Monday - Friday only.';
        }
        else if (valid_days_count == 4 && is_valid_friday == false && is_valid_saturday == false && is_valid_sunday == false) {
           valid_days_string = 'Offer good Monday - Thursday only.';
        } 
        else if (valid_days_count == 3 && is_valid_friday == true && is_valid_saturday == true && is_valid_sunday == true) {
           valid_days_string = 'Offer good Friday, Saturday and Sunday only.';
        }
        else if (valid_days_count == 2 && is_valid_friday == true && is_valid_saturday == true) {
           valid_days_string = 'Offer good Friday and Saturday only.';
        }
        else if (valid_days_count == 2 && is_valid_saturday == true && is_valid_sunday == true) {
           valid_days_string = 'Offer good Saturday and Sunday only.';
        }
        else {
            valid_days_string = 'Offer valid '
            if (is_valid_monday == true) {
                valid_days_string = valid_days_string + 'Monday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Monday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_tuesday == true) {
                valid_days_string = valid_days_string + 'Tuesday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Tuesday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_wednesday == true) {
                valid_days_string = valid_days_string + 'Wednesday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Wednesday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_thursday == true) {
                valid_days_string = valid_days_string + 'Thursday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Thursday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_friday == true) {
                valid_days_string = valid_days_string + 'Friday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Friday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_saturday == true) {
                valid_days_string = valid_days_string + 'Saturday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Saturday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
            if (is_valid_sunday == true) {
                valid_days_string = valid_days_string + 'Sunday';
                valid_days_temp_count = valid_days_temp_count - 1;
                valid_days_string = add_to_string_based_on_count('Sunday', valid_days_string, valid_days_count, valid_days_temp_count);
            }
        }
        return valid_days_string;
    }

    function add_to_string_based_on_count(day, valid_days_string, valid_days_count, valid_days_temp_count) {
        // valid_days_temp_count == 1
        if (valid_days_count != valid_days_temp_count) {
            if (valid_days_temp_count > 1 && valid_days_count != 6) {
                valid_days_string = valid_days_string + ', ';
            }
            else if (valid_days_temp_count == 1) {
                valid_days_string = valid_days_string + ' and ';
            }
            else {
                valid_days_string = valid_days_string + ' only.';
            }
        }        
        return valid_days_string;
    }

    $(".monfri").change(function(){
        valid_days = check_valid_days();
        $(".valid_days").html(valid_days);
    });

    $(".weekend").change(function(){
        valid_days = check_valid_days();
        $(".valid_days").html(valid_days);
    });

});
