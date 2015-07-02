function openWindow(url)
{
    mywindow = window.open(url, "name", "location=0,status=0,scrollbars=0,width=535,height=250, left=500,top=500");
    if (window.focus) {mywindow.focus()}
    return false;
}

