
// Synth sounds for ATM Simulator
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playTone(freq, type, duration, vol=0.1) {
    if(!document.getElementById('sound-toggle').checked) return;
    if(audioCtx.state === 'suspended') audioCtx.resume();
    
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(freq, audioCtx.currentTime);
    
    gainNode.gain.setValueAtTime(vol, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.start();
    oscillator.stop(audioCtx.currentTime + duration);
}

function atmSound(type) {
    if(!document.getElementById('sound-toggle').checked) return;
    
    switch(type) {
        case 'beep':
            playTone(800, 'sine', 0.1, 0.1);
            break;
        case 'error':
            playTone(300, 'sawtooth', 0.3, 0.2);
            setTimeout(() => playTone(300, 'sawtooth', 0.3, 0.2), 150);
            break;
        case 'processing':
            // simulate mechanical processing sound
            let count = 0;
            const intv = setInterval(() => {
                playTone(150 + Math.random()*50, 'square', 0.05, 0.05);
                count++;
                if(count > 10) clearInterval(intv);
            }, 100);
            break;
        case 'cash':
            // simulate cash dispensing
            let c = 0;
            const cintv = setInterval(() => {
                playTone(200, 'noise' || 'sawtooth', 0.1, 0.1);
                c++;
                if(c > 15) clearInterval(cintv);
            }, 150);
            break;
        case 'print':
            let p = 0;
            const pintv = setInterval(() => {
                playTone(600, 'square', 0.02, 0.02);
                p++;
                if(p > 30) clearInterval(pintv);
            }, 50);
            break;
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    // Clock
    setInterval(() => {
        const d = new Date();
        document.getElementById('datetime-display').innerText = d.toLocaleString();
    }, 1000);

    // Hardware buttons to screen clicks
    const setupSideBtns = (side) => {
        for(let i=1; i<=4; i++) {
            const btn = document.getElementById(`btn-${side}${i}`);
            if(btn) {
                btn.addEventListener('click', () => {
                    atmSound('beep');
                    // Find corresponding button on screen if any
                    // We assume menu-row maps to buttons
                    const rows = document.querySelectorAll('.menu-row');
                    if(rows.length >= i) {
                        const targetClass = side === 'L' ? '.l-btn' : '.r-btn';
                        const targetBtn = rows[i-1].querySelector(targetClass);
                        if(targetBtn) targetBtn.click();
                    }
                });
            }
        }
    };
    setupSideBtns('L');
    setupSideBtns('R');

    // Keypad binding
    document.querySelectorAll('.keys-grid button').forEach(btn => {
        btn.addEventListener('click', () => {
            atmSound('beep');
            let val = btn.getAttribute('data-val');
            let action = btn.getAttribute('data-action');
            let keyEmit = val !== null ? val : (action ? action.toUpperCase() : null);
            
            if(keyEmit) {
                const event = new CustomEvent('atm-key', { detail: { key: keyEmit } });
                window.dispatchEvent(event);
            }
        });
    });

    // Handle physical keyboard too
    document.addEventListener('keydown', (e) => {
        if(e.key >= '0' && e.key <= '9') {
            window.dispatchEvent(new CustomEvent('atm-key', { detail: { key: e.key } }));
        } else if (e.key === 'Enter') {
            window.dispatchEvent(new CustomEvent('atm-key', { detail: { key: 'ENTER' } }));
        } else if (e.key === 'Backspace' || e.key === 'Delete') {
            window.dispatchEvent(new CustomEvent('atm-key', { detail: { key: 'CLEAR' } }));
        } else if (e.key === 'Escape') {
            window.dispatchEvent(new CustomEvent('atm-key', { detail: { key: 'CANCEL' } }));
        }
    });

    // Auto-hide flashes
    setTimeout(() => {
        const flashes = document.getElementById('flash-messages-container');
        if(flashes) flashes.style.display = 'none';
    }, 5000);
    
    // Idle timeout logic if logged in
    if(window.ATM_GLOBALS && window.ATM_GLOBALS.isLoggedIn) {
        let idleTime = 0;
        const resetIdle = () => { idleTime = 0; };
        
        window.addEventListener('mousemove', resetIdle);
        window.addEventListener('keypress', resetIdle);
        window.addEventListener('atm-key', resetIdle);
        window.addEventListener('click', resetIdle);
        
        setInterval(() => {
            idleTime++;
            if(idleTime >= 60) { // 60 seconds of inactivity
                alert("Session expired due to inactivity.");
                window.location.href = window.ATM_GLOBALS.logoutUrl;
            }
        }, 1000);
    }
});

function atmLogout() {
    atmSound('processing');
    
    // Eject card visually
    const hardwareCard = document.getElementById('card-visual');
    if(hardwareCard) {
        hardwareCard.style.display = 'block';
        setTimeout(() => {
            hardwareCard.style.top = '-20px';
        }, 50);
    }
    
    setTimeout(() => {
        window.location.href = window.ATM_GLOBALS.logoutUrl;
    }, 1500);
}
