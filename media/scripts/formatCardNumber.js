function formatCardNumber(inputBox,ek,ew)
{
    // Format the credit card number as the user types it. 
    // Insert dash every 4 numbers
    var myEvent = 9;
     var filteredInput = "";
     var spread = 0;
     var x = '';
     var amexInterceptCounter = 1;
     var dashIntercept = 4;
    var tempText = inputBox.value.substring(0,19);
    var filterType = "0123456789";
     if (ew != null)//mozilla-type browsers
    {
        myEvent = ew;
    }
    else if (ek != null)//IE-type browsers
    {
        myEvent = ek;
    }
    if (myEvent != 0 && myEvent != 8 && myEvent != 9 && myEvent != 37 && myEvent != 38 && myEvent != 39 && myEvent != 40 && myEvent != 46)
    {
        typedChar = String.fromCharCode(myEvent)
        if (filterType.indexOf(typedChar) == -1)
           {
           return false;
           }
      }
    if (myEvent != 8 && myEvent != 46)//delete and backspace
    {
       if (tempText.substring(0,1) == 3) //amex
       {
           for (i=0; i < tempText.length; i++) 
            {
                x = tempText.charAt(i);
                if (filterType.indexOf(x) != -1)
                {
                    filteredInput = filteredInput + x;
                    spread += 1;
                    if (spread == dashIntercept && i < 16)
                    {
                        spread = 0;
                        filteredInput = filteredInput + '-'
                        amexInterceptCounter += 1;
                        if (amexInterceptCounter == 2)
                            dashIntercept = 6;
                        else
                            dashIntercept = 5;
                    }
                }   
            }
       }
       else
       {
            for (i=0; i < tempText.length; i++) 
            {
                x = tempText.charAt(i);
                if (filterType.indexOf(x) != -1)
                {
                    filteredInput = filteredInput + x;
                    spread += 1;
                    if (spread == dashIntercept && i < 16)
                    {
                        spread = 0;
                        filteredInput = filteredInput + '-'
                    }
                }    
            }
        }
        if (filteredInput == "-")
        {
            filteredInput = "";
        }
        else if (filteredInput.substring(filteredInput.length-1) == '-')
        {
            filteredInput = filteredInput.substring(0,filteredInput.length-1);
        }
        inputBox.value = filteredInput;
        return true;
        
    }
  }