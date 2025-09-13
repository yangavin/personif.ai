const WebSocket = require('ws');
const express = require('express');
const path = require('path');
const recorder = require('node-record-lpcm16');
const mic = require('mic');
const querystring = require('querystring');
require('dotenv').config();

class CharacterAssistantServer {
    constructor() {
        this.app = express();
        this.server = require('http').createServer(this.app);
        this.wss = new WebSocket.Server({ server: this.server });
        this.currentCharacter = 'harvey_specter';
        
        // AssemblyAI Configuration
        this.ASSEMBLY_API_KEY = "bdf0002c857f452dac6670c41392a68a";
        this.CONNECTION_PARAMS = {
            sampleRate: 16000,
            formatTurns: true,
            endOfTurnConfidenceThreshold: 0.7,
            minEndOfTurnSilenceWhenConfident: 160,
            maxTurnSilence: 2400,
            keytermsPrompt: []
        };
        this.ASSEMBLY_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws";
        this.ASSEMBLY_ENDPOINT = `${this.ASSEMBLY_ENDPOINT_BASE_URL}?${querystring.stringify(this.CONNECTION_PARAMS)}`;
        
        // Audio configuration
        this.SAMPLE_RATE = 16000;
        this.CHANNELS = 1;
        
        this.setupExpress();
        this.setupWebSocketServer();
    }

    setupExpress() {
        this.app.use(express.static(path.join(__dirname, 'public')));
        
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'public', 'index.html'));
        });
    }

    setupWebSocketServer() {
        this.wss.on('connection', (clientWs) => {
            console.log('🎧 Client connected - ready for earbud session');
            
            let assemblyWs = null;
            let recording = null;
            let micInputStream = null;
            let isListening = false;
            let currentCharacter = this.currentCharacter;
            
            // Send welcome message
            clientWs.send(JSON.stringify({
                type: 'status',
                message: 'Connected! Ready to listen through your microphone.'
            }));
            
            clientWs.on('message', async (message) => {
                try {
                    // Handle binary audio data
                    if (message instanceof Buffer && assemblyWs && assemblyWs.readyState === WebSocket.OPEN) {
                        // Forward raw audio data directly to AssemblyAI
                        console.log(`🎵 Forwarding ${message.length} bytes of audio data to AssemblyAI`);
                        assemblyWs.send(message);
                        return;
                    }

                    // Handle JSON messages
                    const data = JSON.parse(message.toString());
                    
                    if (data.type === 'startListening') {
                        console.log('🎤 Starting listening session...');
                        currentCharacter = data.character || currentCharacter;

                        if (data.mode === 'browser-audio') {
                            console.log('🌐 Using browser-based audio capture');

                            // Create AssemblyAI WebSocket connection for browser audio
                            assemblyWs = new WebSocket(this.ASSEMBLY_ENDPOINT, {
                                headers: {
                                    Authorization: this.ASSEMBLY_API_KEY,
                                },
                            });

                            assemblyWs.on('open', () => {
                                console.log('✅ AssemblyAI WebSocket connected for browser audio');
                                clientWs.send(JSON.stringify({
                                    type: 'status',
                                    message: 'Speech recognition ready. Browser will handle audio capture.'
                                }));
                            });

                            assemblyWs.on('message', (assemblyMessage) => {
                                console.log('📨 Received AssemblyAI message:', assemblyMessage.toString());
                                this.handleAssemblyAIMessage(clientWs, assemblyMessage, currentCharacter);
                            });

                            assemblyWs.on('error', (error) => {
                                console.error('❌ AssemblyAI WebSocket Error:', error);
                                clientWs.send(JSON.stringify({
                                    type: 'error',
                                    message: 'Speech recognition error - check your connection'
                                }));
                            });

                            assemblyWs.on('close', () => {
                                console.log('🔌 AssemblyAI WebSocket closed');
                            });
                        } else {
                            // Fallback to server-side audio (will likely fail on Windows without SoX)
                            console.log('🖥️ Attempting server-side audio capture...');
                            // ... existing server-side code
                        }
                    }

                    
                    if (data.type === 'stopListening') {
                        console.log('⏹️ Stopping listening session...');
                        isListening = false;
                        this.cleanup(recording, assemblyWs);
                        
                        clientWs.send(JSON.stringify({
                            type: 'status',
                            message: 'Stopped listening. Ready to start again.'
                        }));
                    }
                    
                    if (data.type === 'setCharacter') {
                        currentCharacter = data.character;
                        console.log(`🎭 Character set to: ${this.getCharacterDisplayName(currentCharacter)}`);
                        
                        clientWs.send(JSON.stringify({
                            type: 'status',
                            message: `Character selected: ${this.getCharacterDisplayName(currentCharacter)}`
                        }));
                    }
                    
                } catch (error) {
                    console.error('❌ Error processing client message:', error);
                }
            });

            clientWs.on('close', () => {
                console.log('👋 Client disconnected');
                this.cleanup(recording, assemblyWs);
            });
        });
    }

    startMicrophone(clientWs, assemblyWs) {
        // Try multiple microphone approaches for better Windows compatibility
        return this.tryMicrophoneApproaches(clientWs, assemblyWs);
    }

    async tryMicrophoneApproaches(clientWs, assemblyWs) {
        console.log('🎙️ Starting microphone with multiple fallback approaches...');

        // Approach 1: Try the mic library (better Windows support)
        try {
            return await this.startMicrophoneWithMicLib(clientWs, assemblyWs);
        } catch (error) {
            console.log('📢 Mic library failed, trying node-record-lpcm16...');
        }

        // Approach 2: Try node-record-lpcm16 as fallback
        try {
            return await this.startMicrophoneWithRecorder(clientWs, assemblyWs);
        } catch (error) {
            console.error('❌ All microphone approaches failed');
            clientWs.send(JSON.stringify({
                type: 'error',
                message: 'Unable to start microphone. Please ensure: 1) Microphone is connected and working, 2) No other apps are using it, 3) Microphone permissions are granted in Windows settings, 4) Try running as administrator.'
            }));
            return null;
        }
    }

    async startMicrophoneWithMicLib(clientWs, assemblyWs) {
        return new Promise((resolve, reject) => {
            try {
                console.log('🎙️ Trying mic library approach...');

                const micInstance = mic({
                    rate: this.SAMPLE_RATE,
                    channels: this.CHANNELS,
                    debug: false,
                    exitOnSilence: 6,
                    fileType: 'wav'
                });

                const micInputStream = micInstance.getAudioStream();
                let hasStarted = false;
                let errorTimeout;

                // Set a timeout to detect if microphone fails to start
                errorTimeout = setTimeout(() => {
                    if (!hasStarted) {
                        console.error('🚨 Mic library timeout');
                        reject(new Error('Mic library timeout'));
                    }
                }, 5000);

                micInputStream.on('data', (audioData) => {
                    if (!hasStarted) {
                        hasStarted = true;
                        clearTimeout(errorTimeout);
                        console.log('✅ Microphone started successfully with mic library');
                        clientWs.send(JSON.stringify({
                            type: 'status',
                            message: `🎤 Listening as ${this.getCharacterDisplayName()} through your microphone!`
                        }));
                        resolve(micInstance);
                    }

                    if (assemblyWs && assemblyWs.readyState === WebSocket.OPEN) {
                        assemblyWs.send(audioData);
                    }
                });

                micInputStream.on('error', (err) => {
                    clearTimeout(errorTimeout);
                    console.error('🚨 Mic library error:', err);
                    reject(err);
                });

                micInputStream.on('silence', () => {
                    console.log('🔇 Silence detected');
                });

                // Start the microphone
                micInstance.start();
                console.log('🎙️ Mic library start command sent...');

            } catch (error) {
                console.error('❌ Mic library setup error:', error);
                reject(error);
            }
        });
    }

    async startMicrophoneWithRecorder(clientWs, assemblyWs) {
        return new Promise((resolve, reject) => {
            try {
                console.log('🎙️ Trying node-record-lpcm16 approach...');

                const recording = recorder.record({
                    sampleRate: this.SAMPLE_RATE,
                    channels: this.CHANNELS,
                    audioType: 'wav',
                    silence: '2.0',
                    threshold: 0.5,
                    verbose: false,
                    device: null
                });

                const micInputStream = recording.stream();
                let hasStarted = false;
                let errorTimeout;

                errorTimeout = setTimeout(() => {
                    if (!hasStarted) {
                        console.error('🚨 Recorder timeout');
                        reject(new Error('Recorder timeout'));
                    }
                }, 5000);

                micInputStream.on('data', (audioData) => {
                    if (!hasStarted) {
                        hasStarted = true;
                        clearTimeout(errorTimeout);
                        console.log('✅ Microphone started successfully with recorder');
                        clientWs.send(JSON.stringify({
                            type: 'status',
                            message: `🎤 Listening as ${this.getCharacterDisplayName()} through your microphone!`
                        }));
                        resolve(recording);
                    }

                    if (assemblyWs && assemblyWs.readyState === WebSocket.OPEN) {
                        assemblyWs.send(audioData);
                    }
                });

                micInputStream.on('error', (err) => {
                    clearTimeout(errorTimeout);
                    console.error('🚨 Recorder error:', err);
                    reject(err);
                });

                recording.start();
                console.log('🎙️ Recorder start command sent...');

            } catch (error) {
                console.error('❌ Recorder setup error:', error);
                reject(error);
            }
        });
    }

    async handleAssemblyAIMessage(clientWs, message, character) {
        try {
            const data = JSON.parse(message);
            const msgType = data.type;

            if (msgType === 'Begin') {
                const sessionId = data.id;
                console.log(`🚀 AssemblyAI session began: ID=${sessionId}`);
                
                clientWs.send(JSON.stringify({
                    type: 'status',
                    message: '👂 Listening through your earbuds - speak naturally!'
                }));
                
            } else if (msgType === 'Turn') {
                const transcript = data.transcript || '';
                const formatted = data.turn_is_formatted;

                if (formatted && transcript.trim().length > 0) {
                    console.log(`📝 Transcript: "${transcript}"`);
                    
                    // Send transcript to client
                    clientWs.send(JSON.stringify({
                        type: 'transcript',
                        text: transcript
                    }));
                    
                    // Generate character response
                    const response = await this.generateCharacterResponse(transcript, character);
                    
                    console.log(`🎭 ${this.getCharacterDisplayName(character)} responds: "${response}"`);
                    
                    clientWs.send(JSON.stringify({
                        type: 'response',
                        text: response,
                        character: character
                    }));
                    
                } else if (transcript.trim().length > 0) {
                    // Partial transcript - show in real-time
                    clientWs.send(JSON.stringify({
                        type: 'partialTranscript',
                        text: transcript
                    }));
                }
                
            } else if (msgType === 'Termination') {
                const audioDuration = data.audio_duration_seconds;
                console.log(`🏁 AssemblyAI session terminated: Duration=${audioDuration}s`);
            }
            
        } catch (error) {
            console.error('❌ Error handling AssemblyAI message:', error);
        }
    }

    async generateCharacterResponse(transcript, character) {
        // Smart contextual responses
        const responses = this.getSmartResponse(transcript, character);
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        return randomResponse;
        
        /* 
        // Uncomment this when you get OpenAI API key:
        try {
            const characterPrompts = {
                harvey_specter: `You are Harvey Specter from Suits. Someone just said: "${transcript}". Respond as Harvey would - confident, witty, sharp, and brief. Keep it under 15 words.`,
                sherlock_holmes: `You are Sherlock Holmes. Someone said: "${transcript}". Respond with deductive reasoning and Victorian eloquence, under 15 words.`,
                tony_stark: `You are Tony Stark/Iron Man. Someone said: "${transcript}". Respond with wit, intelligence, and Tony's confidence, under 15 words.`
            };

            const response = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'gpt-3.5-turbo',
                    messages: [{
                        role: 'user',
                        content: characterPrompts[character]
                    }],
                    max_tokens: 50,
                    temperature: 0.8
                })
            });

            const data = await response.json();
            return data.choices[0].message.content.trim();
        } catch (error) {
            console.error('Error generating response:', error);
            return "I didn't quite catch that.";
        }
        */
    }

    getSmartResponse(transcript, character) {
        const lowerTranscript = transcript.toLowerCase();
        
        // Contextual responses based on what user said
        const contextualResponses = {
            harvey_specter: {
                default: [
                    "That's what I do - I win. What's your next move?",
                    "I don't get lucky, I make my own luck.",
                    "When you're good at what I do, winning isn't luck.",
                    "I'm Harvey Specter. I don't lose.",
                    "What did you just say to me?",
                    "I solve problems. That's what I do."
                ],
                greeting: ["What did you just say to me?", "I'm Harvey Specter, nice to meet you."],
                problem: ["I solve problems. What's the situation?", "Let me handle this one.", "That's what I do."],
                question: ["That's a good question. Here's what we do.", "I've got this handled."],
                work: ["Work? This isn't work. This is what I do.", "Let's close this deal."],
                help: ["I don't need help. I am the help.", "You came to the right person."]
            },
            sherlock_holmes: {
                default: [
                    "Elementary, my dear fellow. The solution is quite obvious.",
                    "The game is afoot! What clues have you observed?",
                    "When you eliminate the impossible, what remains is truth.",
                    "I observe everything. You see, but do not observe.",
                    "The facts are before us, we need only interpret them."
                ],
                greeting: ["Good day. What mystery brings you here?", "Ah, a new case presents itself."],
                problem: ["A most intriguing problem. Let me deduce the solution.", "The facts, please. Give me the facts."],
                question: ["An excellent question. The answer lies in observation.", "Deduce, don't assume."],
                mystery: ["Most fascinating! The plot thickens considerably.", "The clues are all here, we need only see them."],
                help: ["Of course I shall assist. What are the particulars?", "I live to solve such puzzles."]
            },
            tony_stark: {
                default: [
                    "Genius, billionaire, playboy, philanthropist at your service.",
                    "I am Iron Man. What's the problem we're solving?",
                    "Sometimes you gotta run before you can walk.",
                    "The future is coming, and sooner than you think.",
                    "I prefer the weapon you only need to fire once."
                ],
                greeting: ["Hey there. Tony Stark, but you probably knew that.", "What's up? Need some tech advice?"],
                problem: ["Problems are just solutions waiting to happen.", "I'll build something to fix that."],
                question: ["Great question. Let me think... Got it!", "FRIDAY, run diagnostics on that idea."],
                tech: ["Now we're talking tech. That's my specialty.", "I've got just the gadget for that."],
                help: ["Help is my middle name. Well, technically it's Edward.", "What do you need? I've got everything."]
            }
        };

        const charResponses = contextualResponses[character];
        
        // Check for context keywords
        if (lowerTranscript.includes('hello') || lowerTranscript.includes('hi') || lowerTranscript.includes('hey')) {
            return charResponses.greeting || charResponses.default;
        } else if (lowerTranscript.includes('help') || lowerTranscript.includes('assist')) {
            return charResponses.help || charResponses.default;
        } else if (lowerTranscript.includes('problem') || lowerTranscript.includes('issue') || lowerTranscript.includes('trouble')) {
            return charResponses.problem || charResponses.default;
        } else if (lowerTranscript.includes('?') || lowerTranscript.includes('what') || lowerTranscript.includes('how') || lowerTranscript.includes('why')) {
            return charResponses.question || charResponses.default;
        } else if (character === 'sherlock_holmes' && (lowerTranscript.includes('mystery') || lowerTranscript.includes('case'))) {
            return charResponses.mystery || charResponses.default;
        } else if (character === 'tony_stark' && (lowerTranscript.includes('tech') || lowerTranscript.includes('build') || lowerTranscript.includes('invent'))) {
            return charResponses.tech || charResponses.default;
        } else if (character === 'harvey_specter' && lowerTranscript.includes('work')) {
            return charResponses.work || charResponses.default;
        }

        return charResponses.default;
    }

    cleanup(recording, assemblyWs) {
        if (recording) {
            try {
                // Handle both mic library and recorder library
                if (typeof recording.stop === 'function') {
                    recording.stop();
                } else if (typeof recording.pause === 'function') {
                    recording.pause();
                }
                console.log('🔇 Microphone stopped');
            } catch (error) {
                console.error('❌ Error stopping microphone:', error);
            }
        }

        if (assemblyWs && [WebSocket.OPEN, WebSocket.CONNECTING].includes(assemblyWs.readyState)) {
            try {
                if (assemblyWs.readyState === WebSocket.OPEN) {
                    const terminateMessage = { type: 'Terminate' };
                    assemblyWs.send(JSON.stringify(terminateMessage));
                }
                assemblyWs.close();
                console.log('🔌 AssemblyAI WebSocket closed');
            } catch (error) {
                console.error('❌ Error closing AssemblyAI WebSocket:', error);
            }
        }
    }

    getCharacterDisplayName(character) {
        const names = {
            harvey_specter: 'Harvey Specter',
            sherlock_holmes: 'Sherlock Holmes',
            tony_stark: 'Tony Stark'
        };
        return names[character] || 'Unknown Character';
    }

    start(port = 3000) {
        this.server.listen(port, () => {
            console.log('\n🎭 CHARACTER EARBUD ASSISTANT SERVER READY');
            console.log(`🌐 Server running on http://localhost:${port}`);
            console.log('🎧 Using browser-based audio capture');
            console.log('🤖 AssemblyAI real-time transcription enabled');
            console.log('📱 Open the URL above in your browser to start\n');
            console.log('💡 Make sure your microphone is connected and working!');
            console.log('🔧 This version uses browser audio - no SoX required!');
        });
    }
}

const server = new CharacterAssistantServer();
server.start();