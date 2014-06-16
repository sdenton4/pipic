    function formvalues(formid){
        var values = {};
        $.each($(formid).serializeArray(), function(i, field) {
            values[field.name] = field.value;
        });
        return values
    }

    function baseurl() {
        path=document.URL
        path=path.replace( "djpilapp/", "" )
        path=path.replace( "#", "" )
        return path
    };

    function loadImage() {
        $('#imageFrame').fadeTo('fast', 0.5);
        path=baseurl()+"static/new.jpg"
        //width=320;
        //height=240;
        target='#imageFrame';
        X=$('<img src="'+ path +'" id="lastImage" class="img-responsive">')//.width(width).height(height);
        $(target).html(X);
        $('#imageFrame').fadeTo('fast', 1.0);
    }

    function saveProjSettings() {
        vals=formvalues('#projectForm')
        $.ajax(
            url=baseurl()+"djpilapp/saveproj/",
            settings={ 
              data:vals,
              type:"POST"
            }
        );
    }


    //Stack to place requests to the server on.
    functionStack=[]

    function formToJSON(){
        var o ={};
        for( var i=0; i<o.length; i++){
            o[name] = array[i]
        };
    };



    $(document).ready( function(){
        
        //Navigation buttons.
        $('.photoButton').click(function(){
            vals=formvalues('#photoForm')
            iso=vals['formiso']
            ss=vals['formshutterspeed']
            url=baseurl()+'djpilapp/shoot/'+ss+'/'+iso+'/'
            console.log(url)
            waittime=ss/1000+500
            $.ajax(url).done( function(){
                $('#imageFrame').fadeTo('fast', 0.5);
                setTimeout(function(){
                    functionStack.push( loadImage );
                },waittime);    
            });
        });
<<<<<<< HEAD
        
        $('#newProjectSubmit').click(function(){
            event.preventDefault();
            
            var settings = $('#newProjectForm').serializeJSON();
            console.log(settings);
            console.log(baseurl()+'djpilapp/newProject/')
            $.ajax({
                type: "POST",
                url: baseurl()+'djpilapp/newProject/',
                data: settings,
                success: function(data){
                    $('#newPName').text(data);
                    $('#newProjectAlert').show('slow');
                }

            });
            
            
                                    
        });            //$.post(url)...
            //Post https://api.jquery.com/jQuery.post/ to submit the JSON object via the newProject request

        
        
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });
        
        //Toggles for views
=======
        $('#alertBox').hide()
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });
        $('.projSaveButton').click(function(){
            functionStack.push( saveProjSettings );
        });

>>>>>>> celery
        $('#overviewBtn').click(function(){
            event.preventDefault();
            $('#rvwProjects').hide();
            $('#newProject').hide();
            $('#overview').show();
        });
        $('#rvwProjectBtn').click(function(){
            event.preventDefault();
            $('#overview').hide();
            $('#newProject').hide();
            $('#rvwProjects').show();
        });
        
        $('#newProjectBtn').click(function(){
            event.preventDefault();
            $('#rvwProjects').hide();
            $('#overview').hide();
            $('#newProject').show();
        });
        $('.calibrateButton').click(function(){
            url=baseurl()+'djpilapp/findinitialparams/'
            $.ajax(url);
        });
        $('.lapseButton').click(function(){
            url=baseurl()+'djpilapp/startlapse/'
            $.ajax(url);
        });
        $('.deactivateButton').click(function(){
            url=baseurl()+'djpilapp/deactivate/'
            $.ajax(url);
        });

        $('#confirm_box').toggle()

        $('.rebootButton').click(function(){
            $('#confirm_box').html(
            "Are you sure you want to reboot?<br /><button class='btn btn-danger' id='rebootReal'>Reboot</button>")
            $('#confirm_box').toggle()
            $('#rebootReal').click(function(){
                url=baseurl()+'djpilapp/reboot/'
                $.ajax(url);
            });
        });

        $('.poweroffButton').click(function(){
            $('#confirm_box').html(
            "Are you sure you want to power down?<br /><button class='btn btn-danger' id='poweroffReal'>Power Off</button>")
            $('#confirm_box').toggle()
            $('#poweroffReal').click(function(){
            url=baseurl()+'djpilapp/poweroff/'
                $.ajax(url);
            });
        });

        $('.deleteButton').click(function(){
            $('#confirm_box').html(
            "Are you sure you want to delete all stored pictures?<br /><button class='btn btn-danger' id='deleteReal'>Delete All</button>")
            $('#confirm_box').toggle()
            $('#deleteReal').click(function(){
            url=baseurl()+'djpilapp/deleteall/'
                $.ajax(url);
            });
        });


        //Page Updates
        setInterval(function() {
            if (functionStack.length>0) {
                f = functionStack.pop();
                //console.log(f);
                f();
            }
            else {
                path=baseurl()+'djpilapp/jsonupdate/';
                $.ajax(
                  url=path,
                  settings={
                  dataType: "json",
                  success: function(data){
                      if (data['lastshot']!=$('#pilapse_lastshot').html()){
                          functionStack.push( loadImage );
                      };
                      $('#alertBox').hide()
                      $('#jsontarget').html(data['time']);
                      $('#diskfree').html(data['diskfree']);
                      $('#remaining').html(data['remaining']);
                      $('#pilapse_ss').html(data['ss']);
                      $('#pilapse_iso').html(data['iso']);
                      $('#pilapse_lastbr').html(data['lastbr']);
                      $('#pilapse_avgbr').html(data['avgbr']);
                      $('#pilapse_status').html(data['status']);
                      $('#pilapse_shots').html(data['shots']);
                      $('#pilapse_lastshot').html(data['lastshot']);
                      $('#project_interval').html(data['interval']);
                      $('#project_brightness').html(data['brightness']);
                      $('#project_width').html(data['width']);
                      $('#project_height').html(data['height']);
                      $('#project_delta').html(data['delta']);
                      $('#project_brightness').html(data['brightness']);
                      if (data['active']==false){
                          $('#pilapse_active').html('False');
                          $('.activebutton').fadeTo(0.5, 1.0);
                          $('.activebutton').removeClass('btn-disabled');
                      } else { 
                          $('#pilapse_active').html('True');
                          $('.activebutton').fadeTo(0.5, 0.2);
                          $('.activebutton').addClass('btn-disabled');
                      };
                    },
                  error: function(data){ $('#alertBox').show() }
                });
              }
        }, 2000);
        //Begin code for dealing with Cross Site Request Forgery Protection
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        var csrftoken = getCookie('csrftoken');
        
        
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        function sameOrigin(url) {
            // test that a given url is a same-origin URL
            // url could be relative or scheme relative or absolute
            var host = document.location.host; // host + port
            var protocol = document.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                    // Send the token to same-origin, relative URLs only.
                    // Send the token only if the method warrants CSRF protection
                    // Using the CSRFToken value acquired earlier
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        
        
        
    });//end document.ready
