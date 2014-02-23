function loadImage(path, width, height, target) {
        X=$('<img src="'+ path +'">').width(width).height(height);
        $(target).html(X);
    }

    $(document).ready( function(){
        //Navigation buttons.
        $('.photoButton').click(function(){
            path=document.URL+"static/new.jpg"
            path=path.replace( "djpilapp/", "" )
            iso=photoForm.elements['iso'].value
            ss=photoForm.elements['shutterspeed'].value*100
            url=document.URL+'shoot/'+ss+'/'+iso+'/'
            console.log(url)
            waittime=ss/100+1000
            $.ajax(url).done( function(){
                setTimeout(function(){loadImage(path,320,240,"#imageFrame")},waittime);
            });
        });
        $('.refreshButton').click(function(){
            path=document.URL+"static/new.jpg"
            path=path.replace( "djpilapp/", "" )
            console.log(path)
            loadImage(path,320,240,"#imageFrame")
        });
        $('.navbutton').mouseenter(function(){$(this).fadeTo('slow',1)});
        $('.navbutton').mouseleave(function(){$(this).fadeTo('slow',.5)});
    });