frappe.pages['web-camera'].onload = function(wrapper) {
  frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Web Camera',
    single_column: true
  });

      var cust_name

      if(frappe.route_options){
           cust_name = frappe.route_options.customer_name
        }
      
 this.wrapper= new frappe.Webcam(wrapper,cust_name);

}



frappe.Webcam = Class.extend({
  // var stream;
  init: function(wrapper,cust_name) {
    console.log("in the webcamhgfhgf");
    this.show_menus1(wrapper);
    this.compatibility();
    this.button(wrapper,cust_name);
},
show_menus1:function(wrapper){
   $("<div  style='width:100%;height:100%'>\
    <table style='table-layout:fixed'><tr  style='width:100%;'>\
<td style='width:50%;height:100%'><video id='webcam' style='width:90%;height:90%;padding-left:30px' autoplay='autoplay' controls='true' style='display:inline-block;padding-left:20px'></video><td>\
<td style='width:50%;height:100%'><canvas id='capimage'  style='width:85%;height:70%;padding-left:40px'></canvas></td>\
</tr></table>\
</div></br>\
<div style='display:inline-block;width:100%;height:20%'>\
<button class='btn btn-primary' id='screenshot-button' type='button' style='margin-left:40px'>Take Screenshot</button>\
<button class='btn btn-primary' id='save-button' type='button' style='margin-left:20px'>Save Image</button>\
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
  console.log("in the button");
  $("#screenshot-button").click(function() {
      console.log("in the button");
    me.snapshot(wrapper,cust_name);
  })



},

button2:function(wrapper,validJson,cust_name){
  me=this;
  console.log("In button 2")
  console.log(cust_name)
   $('#save-button').click(function(){
       if(validJson && cust_name){

             frappe.call({
            method:'erpnext.accounts.page.report_template.report_template.webcam_img_upload',
            args:{'imgdata1':validJson,'customer':cust_name},
            callback:function(r){
              console.log("in call")
              console.log(r.message)
              setTimeout(function (){window.location.reload()}, 1000)
             window.history.back();

                   }
            })

           }

   })

},

snapshot:function(wrapper,cust_name) {
               console.log("In snapshot")
              me=this
              var video = document.querySelector('#webcam');
              var button = document.querySelector('#screenshot-button');
              var canvas = document.querySelector('#capimage');
             
              var ctx = canvas.getContext('2d');
              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;
              ctx.drawImage(video,0,0);
              console.log("after drawing image")
              var imgdata=canvas.toDataURL("img/png");
              validJson=JSON.stringify(imgdata)
              me.button2(wrapper,validJson,cust_name)
              // stream.stop();
            
},


});
