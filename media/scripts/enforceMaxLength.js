function enforceMaxLength(field, maxLimit, event)
{
    var e = window.event ? event.keyCode : event.which;
    if ( ((e == 32) || (e == 13) || (e > 47) || (e == undefined)) && field.value.length + 1 > maxLimit )
    {
        field.value = field.value.substring( 0, maxLimit );
        return false;
    }
    else
    { return true; }
}