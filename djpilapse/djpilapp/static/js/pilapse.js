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
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });

        $('#overviewBtn').click(function(){
            event.preventDefault();
            $('#newProject').hide();
            $('#overview').show();
        });
        $('#newProjectBtn').click(function(){
            event.preventDefault();
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
    });
