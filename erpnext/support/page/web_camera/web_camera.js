 var cust_name=''
frappe.pages['web-camera'].onload = function(wrapper) {
  frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Web Camera',
    single_column: true
  });

   frappe.provide("sites.assets.js.cropper.js");
   frappe.provide("sites.assets.js.cropper.css");
      
      if(frappe.route_options){
           cust_name = frappe.route_options.customer_name
           sessionStorage.setItem('key',cust_name);
        }
      else{
           cust_name = sessionStorage.getItem('key');
      }    

     
   this.wrapper= new frappe.Webcam(wrapper,cust_name);   
 

}

frappe.pages['web-camera'].refresh = function(wrapper) {
   if(frappe.route_options){
           cust_name = frappe.route_options.customer_name
           sessionStorage.setItem('key',cust_name);
      }



      
}



frappe.Webcam = Class.extend({
  // var stream;
  init: function(wrapper,cust_name) {
    this.show_menus1(wrapper);
    //this.show_menus(wrapper);
    this.compatibility();
    this.button(wrapper,cust_name);
},
show_menus1:function(wrapper){
   $("<div  style='width:100%;height:100%' class='newcontainer'>\
    <table style='table-layout:fixed'><tr  style='width:100%;'>\
<td style='width:50%;height:100%'><video id='webcam' style='width:90%;height:90%;padding-left:30px' autoplay='autoplay' controls='true' style='display:inline-block;padding-left:20px'></video><td>\
<td style='width:50%;height:100%;maxWidth' id='cropimgdata' ><canvas id='capimage123'  style='width:75%;height:70%;padding-left:40px'></canvas></td>\
</tr></table>\
</div></br>\
<div style='display:inline-block;width:100%;height:20%'>\
<button class='btn btn-primary' id='screenshot-button' type='button' style='margin-left:40px'>Take Screenshot</button>\
</div>").appendTo($(wrapper).find(".layout-main"));

},
compatibility:function(wrapper){
    var video = document.querySelector('#webcam');
                navigator.getUserMedia = (navigator.getUserMedia ||
                                  navigator.webkitGetUserMedia ||
                                  navigator.mozGetUserMedia ||
                                  navigator.msGetUserMedia);
              if (navigator.getUserMedia) {
                    navigator.getUserMedia
                                  (
                                    { video: true },
                                    function (localMediaStream) {
                                        video.src = window.URL.createObjectURL(localMediaStream);
                                        // stream=localMediaStream;
                                    }, onFailure);
                }
                else {
                    alert('OOPS No browser Support');
                }

              function onFailure(err) {
                        alert("The following error occured: " + err.name);
                } 
     // me.button(video);             
                             
},
button:function(wrapper,cust_name){
  me=this;
  $("#screenshot-button").click(function() {
    me.snapshot(wrapper,cust_name);
  })



},

button2:function(wrapper,cust_name){
  me=this;
 
   $('#save-button').click(function(){
      var target_image = document.querySelector('img#target_image');
          var imgdata=$('img#target_image').attr('src');
          validJson=JSON.stringify(imgdata)
       


       if(validJson && cust_name){

             frappe.call({
            method:'erpnext.accounts.page.report_template.report_template.webcam_img_upload',
            args:{'imgdata1':validJson,'customer':cust_name},
            callback:function(r){
              alert("Image Saved Successfully")

                    }
            })

           }

   })

},

snapshot:function(wrapper,cust_name) {
              me=this

              var dialog = new frappe.ui.Dialog({
              width: 700,
              hide_on_page_refresh: true,
              title: __("Image Cropper"),
              fields: [
                  { fieldtype: "HTML",fieldname:'styles_name', label: "list" }
                ]
            });


            var fd = dialog.fields_dict;

              this.table = $(fd.styles_name.wrapper).html("<table style='width:600px;height:300px;table-layout:fixed' id='myid'>\
                 <tr><td style='width:50%;height:100%;'><canvas id='capimage'  style='width:75%;height:70%;padding-left:40px'></canvas></td>\
                <td id='showDataURL' style='display:inline-block;'></td></tr>\
                </table>\
                   <div class='clearfix' >\
              <div class='eg-button' style='width:100%;display:inline-block;margin-top:10px'>\
      <button class='btn btn-primary' id='getDataURL' type='button'>Crope Image</button>\
         <button id='rotateLeft' type='button' class='btn btn-info'>Rotate Left</button>\
        <button id='rotateRight' type='button' class='btn btn-info'>Rotate Right</button>\
      <button class='btn btn-primary' id='save-button' type='button' style='margin-left:20px'>Save Image</button>\
      </div><br>\
      </div><br>")
             dialog.show();
            

            $('div.modal.in').on("hide.bs.modal", function() {

                  $('#myid').empty()
                  $('#myid').remove()

            })

              
              var video = document.querySelector('#webcam');
              var button = document.querySelector('#screenshot-button');
              var canvas = document.querySelector('#capimage');
              
              var ctx = canvas.getContext('2d');
              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;
              ctx.drawImage(video,0,0);
              me.button2(wrapper,cust_name)
              me.get_cropper();
              setTimeout(function(){
                 $('.cropper-container').css("top","0px")

              },1000)
              me.show_functions(wrapper);
            
},

 get_cropper :function(){
              $('canvas#capimage').cropper({
                     aspectRatio: 16 / 9,
                      crop: function(data) {
                           // Output the result data for cropping image.
                      $('.cropper-container').css("top","1px")

                     }
               });


 }, 
  show_functions: function(wrapper) {


    
    var me = this;
    $(function() {
      var $image =$('#capimage'),
          $dataX = $("#dataX"),
          $dataY = $("#dataY"),
          $dataHeight = $("#dataHeight"),
          $dataWidth = $("#dataWidth"),
          console = window.console || {log:$.noop},
          cropper;

      $image.cropper({
        aspectRatio: 16 / 9,
        data: {
          x: 420,
          y: 50,
          width: 640,
          height: 360
        },
        preview: ".preview",

        autoCrop: false,
        dragCrop: false,
        modal: false,
        moveable: false,
        resizeable: false,
        scalable: false,

        maxWidth: 480,
        maxHeight: 270,
        minWidth: 160,
        minHeight: 90,

        done: function(data) {
          $dataX.val(data.x);
          $dataY.val(data.y);
          $dataHeight.val(data.height);
          $dataWidth.val(data.width);
        },
        build: function(e) {
          // console.log(e.type);
        },
        built: function(e) {
          // console.log(e.type);
        },
        dragstart: function(e) {
          // console.log(e.type);
        },
        dragmove: function(e) {
          // console.log(e.type);
        },
        dragend: function(e) {
          // console.log(e.type);
        }
      });

      me.cropper = $image.data("cropper");

      $image.on({
        "build.cropper": function(e) {
          // console.log(e.type);
          // e.preventDefault();
        },
        "built.cropper": function(e) {
          // console.log(e.type);
          // e.preventDefault();
        },
        "dragstart.cropper": function(e) {
          // console.log(e.type);
          // e.preventDefault();
        },
        "dragmove.cropper": function(e) {
          // console.log(e.type);
          // e.preventDefault();
        },
        "dragend.cropper": function(e) {
          // console.log(e.type);
          // e.preventDefault();
        }
      });

   

      $("#rotate").click(function() {
        $image.cropper("rotate", $("#rotateWith").val());
      });

      $("button#rotateLeft.btn.btn-info").click(function() {
        $('.cropper-container').css("top","0px")
        $image.cropper("rotate", -90);
        $('div.cropper-container').css({'width':'450px','height':'250px'})
      });

      $("button#rotateRight.btn.btn-info").click(function() {
        $('.cropper-container').css("top","0px")
        $image.cropper("rotate", 90);
      });

      $("#getImageData").click(function() {
        $("#showImageData").val(JSON.stringify($image.cropper("getImageData")));
      });

      $("#setData").click(function() {
        $(this).image.cropper("setData", {
          x: $dataX.val(),
          y: $dataY.val(),
          width: $dataWidth.val(),
          height: $dataHeight.val()
        });
      });

      $("#getData").click(function() {
        var url=$image.cropper("getData")
        $("#showData").val(JSON.stringify($image.cropper("getData")));
      });

      $("button#getDataURL").click(function() {
        var dataURL = $image.cropper("getDataURL");
        //window.open(dataURL);
        $("#dataURL").text(dataURL);
        $("#showDataURL").html('<img id="target_image" src="' + dataURL + '" style="width:250px;height:200px;margin-top:50px;padding-left:10px">');
      });

      $("#getDataURL2").click(function() {
        //alert("#getDataURL2");
        var dataURL = $image.cropper("getDataURL", "image/jpeg");

        $("#dataURL").text(dataURL);
        window.open(dataURL);
        $("#showDataURL").html('<img src="' + dataURL + '" height="50%" width="50%">');
      });


    });   

   }, 



});










