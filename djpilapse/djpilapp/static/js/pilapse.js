    function loadImage() {
        $('#imageFrame').fadeTo('fast', 0.5);
        path=baseurl()+"static/new.jpg"
        width=320;
        height=240;
        target='#imageFrame';
        X=$('<img src="'+ path +'">').width(width).height(height);
        console.log(path);
        $(target).html(X);
        $('#imageFrame').fadeTo('fast', 1.0);
    }

    function updateArticle(page){
      path = baseurl()+ 'djpilapp/' + page +'/';
      console.log(path);
      $.get(path, function(data){
        $('article').html( data );
      });
      ;
    }

    function baseurl() {
        path=document.URL
        path=path.replace( "djpilapp/", "" )
        path=path.replace( "#", "" )
        return path
    };

    //Stack to place requests to the server on.
    functionStack=[]

    $(document).ready( function(){
        //Navigation buttons.
        $('.photoButton').click(function(){
            iso=photoForm.elements['iso'].value
            ss=photoForm.elements['shutterspeed'].value*100
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
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });
        $('#newProjectButton').click(function(){
            event.preventDefault();
            functionStack.push( updateArticle('newProject') );
        });

        $('#homeButton').click(function(){
            functionStack.push( updateArticle('overview') );
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
            }
            else {
                path=baseurl()+'djpilapp/jsonupdate/';
                $.getJSON( path, function( data ) {
                $('#jsontarget').html(data['time']);
              }
            )};
        }, 2000);
    });
