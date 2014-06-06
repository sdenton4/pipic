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
        $('#alertBox').hide()
        $('.refreshButton').click(function(){
            functionStack.push( loadImage );
        });
        $('.projSaveButton').click(function(){
            functionStack.push( saveProjSettings );
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

        $('.rebootButton').click(function(){
            url=baseurl()+'djpilapp/reboot/'
            $.ajax(url);
        });
        $('.poweroffButton').click(function(){
            url=baseurl()+'djpilapp/poweroff/'
            $.ajax(url);
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

        $('.activebutton').mouseenter(function(){$(this).fadeTo('slow',0.75)});
        $('.activebutton').mouseleave(function(){$(this).fadeTo('slow',1.0)});

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
                          console.log(data['lastshot'], $('#pilapse_lastshot').html())
                          functionStack.push( loadImage );
                      };
                      $('#alertBox').hide()
                      $('#jsontarget').html(data['time']);
                      $('#pilapse_ss').html(data['ss']);
                      $('#pilapse_iso').html(data['iso']);
                      $('#pilapse_lastbr').html(data['brightness']);
                      $('#pilapse_shots').html(data['shots']);
                      $('#pilapse_lastshot').html(data['lastshot']);
                      if (data['active']==false){
                          $('#pilapse_active').html('False');
                          $('.photoButton').fadeTo(0.2, 1);
                          $('.photoButton').addClass('activebutton');
                          $('.calibrateButton').fadeTo(0.2, 1);
                          $('.calibrateButton').addClass('activebutton');
                          $('.lapseButton').fadeTo(0.2, 1);
                          $('.lapseButton').addClass('activebutton');
                      } else { 
                          $('#pilapse_active').html('True');
                          $('.photoButton').fadeTo(0.2, 0.2);
                          $('.photoButton').removeClass('activebutton');
                          $('.calibrateButton').fadeTo(0.2, 0.2);
                          $('.calibrateButton').removeClass('activebutton');
                          $('.lapseButton').fadeTo(0.2, 1);
                          $('.lapseButton').removeClass('activebutton');
                      };
                    },
                  error: function(data){ $('#alertBox').show() }
                });
              }
        }, 2000);
    });
