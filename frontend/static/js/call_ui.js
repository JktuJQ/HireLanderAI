var myVideo;

document.addEventListener("DOMContentLoaded", (event)=>{
    myVideo = document.getElementById("local_vid");
    myVideo.onloadeddata = ()=>{console.log("W,H: ", myVideo.videoWidth, ", ", myVideo.videoHeight);};
    var muteBttn = document.getElementById("bttn_mute");
    var muteVidBttn = document.getElementById("bttn_vid_mute");
    var callEndBttn = document.getElementById("call_end");

    muteBttn.addEventListener("click", (event)=>{
        audioMuted = !audioMuted;
        setAudioMuteState(audioMuted);        
    });    
    muteVidBttn.addEventListener("click", (event)=>{
        videoMuted = !videoMuted;
        setVideoMuteState(videoMuted);        
    });    
    callEndBttn.addEventListener("click", (event)=>{
        window.location.replace("/");
    });

   

});


function makeVideoElement(element_id, display_name)
{
    let wrapper_div = document.createElement("div");
    let vid_wrapper = document.createElement("div");
    let vid = document.createElement("video");
    let name_text = document.createElement("div");
    let video_overlay = document.createElement("div");
    let participant_label = document.createElement("span");

    wrapper_div.id = "div_"+element_id +" video-container";
    vid.id = "vid_"+element_id;

    wrapper_div.className = "shadow video-item";
    vid_wrapper.className = "video-wrapper";
    name_text.className = "display-name";
    
    vid.autoplay = true;        
    name_text.innerText = display_name;


    video_overlay.className = "video-overlay";
    participant_label.className = "participant-label";
    participant_label.innerText = display_name;
    
    
    video_overlay.appendChild(participant_label)
    vid_wrapper.appendChild(vid);
    vid_wrapper.appendChild(video_overlay);
    wrapper_div.appendChild(vid_wrapper);
    wrapper_div.appendChild(name_text);

    return wrapper_div;
}

function addVideoElement(element_id, display_name)
{        
    document.getElementById("video_grid").appendChild(makeVideoElement(element_id, display_name));
}
function removeVideoElement(element_id)
{    
    let v = getVideoObj(element_id);
    if(v.srcObject){
        v.srcObject.getTracks().forEach(track => track.stop());
    }
    v.removeAttribute("srcObject");
    v.removeAttribute("src");

    document.getElementById("div_"+element_id).remove();
}

function getVideoObj(element_id)
{
    return document.getElementById("vid_"+element_id);
}

function setAudioMuteState(flag)
{
    let local_stream = myVideo.srcObject;
    local_stream.getAudioTracks().forEach((track)=>{track.enabled = !flag;});
    document.getElementById("mute_icon").innerText = (flag)? "mic_off": "mic";
}
function setVideoMuteState(flag)
{
    let local_stream = myVideo.srcObject;
    local_stream.getVideoTracks().forEach((track)=>{track.enabled = !flag;});
    document.getElementById("vid_mute_icon").innerText = (flag)? "videocam_off": "videocam";
}
