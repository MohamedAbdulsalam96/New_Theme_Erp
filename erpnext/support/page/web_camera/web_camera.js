frappe.pages['web-camera'].onload = function(wrapper) {
  frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Web Camera',
    single_column: true
  });

      var cust_name

      if(frappe.route_options){
           cust_name = frappe.route_options.customer_name
           localStorage.setItem("name",cust_name)
        } 
     
      
 this.wrapper= new frappe.Webcam(wrapper,cust_name);

}



frappe.Webcam = Class.extend({
  init: function(wrapper,cust_name) {
    console.log("in the webcamhgfhgf");
    this.show_menus1(wrapper);
    this.compatibility();
    this.button(wrapper,cust_name);
},
show_menus1:function(wrapper){
   $("<div  style='display:inline-block'>\
  <video id='webcam' width='50%'  height='50%' autoplay='autoplay' controls='true' style='display:inline-block;padding-left:20px'></video>\
<canvas id='capimage'  style='width:400px;height:340px;display:inline-block;padding-left:70px'></canvas></br></br>\
<div>\
<button class='btn btn-primary' id='screenshot-button' type='button' style='margin-left:50px'>Take Screenshot</button>\
<button class='btn btn-primary' id='save-button' type='button' style='margin-left:20px'>Save Image</button>\
</div>\
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
   $('#save-button').click(function(){

    frappe.call({
        method:'erpnext.accounts.page.report_template.report_template.webcam_img_upload',
        args:{'imgdata1':validJson,'customer':cust_name},
        callback:function(r){
          console.log("in call")
          console.log(r.message)
         window.history.back();

               }
            })
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
            
},


});

