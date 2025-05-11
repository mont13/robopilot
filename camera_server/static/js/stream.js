// stream.js: Capture camera/mic and stream to backend
let mediaRecorder;
let ws;
let isStreaming = false;

const preview = document.getElementById('preview');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.getElementById('status');

startBtn.onclick = async () => {
    startBtn.disabled = true;
    stopBtn.disabled = false;
    status.textContent = 'Requesting camera and mic...';
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        preview.srcObject = stream;
        status.textContent = 'Connecting to backend...';
        const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
        ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/stream`);
        ws.binaryType = 'arraybuffer';
        ws.onopen = () => {
            status.textContent = 'Streaming...';
            isStreaming = true;
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm; codecs=vp8,opus' });
            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0 && ws.readyState === 1) {
                    e.data.arrayBuffer().then(buf => ws.send(buf));
                }
            };
            mediaRecorder.start(200); // send every 200ms
        };
        ws.onclose = () => {
            status.textContent = 'WebSocket closed.';
            isStreaming = false;
        };
        ws.onerror = (e) => {
            status.textContent = 'WebSocket error.';
            isStreaming = false;
        };
    } catch (err) {
        status.textContent = 'Error: ' + err;
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
};

stopBtn.onclick = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    if (ws && ws.readyState === 1) ws.close();
    status.textContent = 'Stopped.';
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Reset preview
    if (preview.srcObject) {
        const tracks = preview.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        preview.srcObject = null;
    }
};
