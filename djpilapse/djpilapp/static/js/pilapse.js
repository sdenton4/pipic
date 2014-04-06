    function formvalues(formid){
        var values = {};
        $.each($(formid).serializeArray(), function(i, field) {
            values[field.name] = field.value;
        });
        return values
    }

    function loadImage() {
        $('#imageFrame').fadeTo('fast', 0.5);
        path=baseurl()+"static/new.jpg"
        //width=320;
        //height=240;
        target='#imageFrame';
        X=$('<img src="'+ path +'">')//.width(width).height(height);
        $(target).html(X);
        $('#imageFrame').fadeTo('fast', 1.0);
    }

    function updateArticle(page){
    //This is cruft now.  Delete this function.
      path = baseurl()+ 'djpilapp/' + page +'/';
      console.log(path);
      $.get(path, function(data){
        $('article').html( data );
      });
    }

    function baseurl() {
        path=document.URL
        path=path.replace( "djpilapp/", "" )
        path=path.replace( "#", "" )
        return path
    };

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
            iso=vals['iso']
            ss=vals['shutterspeed']*100
            url=baseurl()+'djpilapp/shoot/'+ss+'/'+iso+'/'
            console.log(url)
            waittime=ss/100+500
            $.ajax(url).done( function(){
                $('#imageFrame').fadeTo('fast', 0.5);
                setTimeout(function(){
                    functionStack.push( loadImage );
                },waittime);    
            });
        });
        
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
                    $('#newProjectSubmit').text(data);
                }

            });
            
            
                                    
        });            //$.post(url)...
            //Post https://api.jquery.com/jQuery.post/ to submit the JSON object via the newProject request

        
        
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });
        
        //Toggles for views
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
        $('.navbutton').mouseenter(function(){$(this).fadeTo('slow',0.75)});
        $('.navbutton').mouseleave(function(){$(this).fadeTo('slow',1.0)});

        //Page Updates
        setInterval(function() {
            if (functionStack.length>0) {
                f = functionStack.pop();
                //console.log(f);
                f();
            }
            else {
                path=baseurl()+'djpilapp/jsonupdate/';
                $.getJSON( path, function( data ) {
                $('#jsontarget').html(data['time']);
              }
            )};
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
