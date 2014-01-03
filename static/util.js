


        $(document).ajaxStop($.unblockUI); 
        $(document).ready(function() {
        // Handler for .ready() called.
        });
        function doSearch() {
            var fkeywords = document.searchform.elements["keywords"].value;
            // Still need to check for success
            $.blockUI({ message: "Searching..." });
           }
        function checkCart() {
                
                    $.ajax({
                      type: 'GET',
                      url: '/cartexists',
                      success: function(data){
                            if (data){
                                if (data == '1') {
                                    $('p#cart').replaceWith('<p><strong><a href="/viewcart">View Cart</a></strong></p>');
                                    }
                                
                                }
                            else
                                {
                                alert("I'm sorry there was a problem checking for a cart.");
                                }
                        }
                    });

            }
        function addToCart() {
                
                listId=document.merchants.elements["merch"].value;
                $.blockUI({message: "Adding to Cart..."}); 
                $.ajax({
                      type: 'GET',
                      url: '/addtocart?listid=',
                      data: listId,
                      success: function(data){
                            if (data){
                                if (data == '0') {
                                        checkCart();
                                    }
                                if (data == '1') {
                                    checkCart();
                                    }
                                }
                            else
                                {
                                alert("I'm sorry there was a problem adding to cart.");
                                }
                            
                        }
                    });
                
                
                //setTimeout(function() { 
                //   $.unblockUI({ 
                //        onUnblock: function(){ alert('Cart functionality not implemented (yet)'); } 
                //    }); 
                //    }, 2000);
                    
                    
                    
        }
