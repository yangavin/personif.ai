const WebSocket = require('ws');
const express = require('express');
const path = require('path');
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
            console.log('🎧 Client connected - ready for browser audio session');

            let assemblyWs = null;
            let currentCharacter = this.currentCharacter;
            
            // Send welcome message
            clientWs.send(JSON.stringify({
                type: 'status',
                message: 'Connected! Ready for browser-based audio streaming.'
            }));
            
            clientWs.on('message', async (message) => {
                try {
                    // Handle binary audio data first
                    if (message instanceof Buffer && assemblyWs && assemblyWs.readyState === WebSocket.OPEN) {
                        // Forward raw audio data directly to AssemblyAI
                        console.log(`🎵 Forwarding ${message.length} bytes of audio data to AssemblyAI`);
                        assemblyWs.send(message);
                        return;
                    }

                    // Try to handle as JSON - if it fails, it's likely binary data
                    let data;
                    try {
                        data = JSON.parse(message.toString());
                    } catch (parseError) {
                        // This is binary audio data, handle it
                        if (assemblyWs && assemblyWs.readyState === WebSocket.OPEN) {
                            console.log(`🎵 Forwarding ${message.length} bytes of binary audio data to AssemblyAI`);
                            assemblyWs.send(message);
                        }
                        return;
                    }
                    
                    if (data.type === 'startListening') {
                        console.log('🎤 Starting simple transcription session...');

                        // Create AssemblyAI WebSocket connection
                        assemblyWs = new WebSocket(this.ASSEMBLY_ENDPOINT, {
                            headers: {
                                Authorization: this.ASSEMBLY_API_KEY,
                            },
                        });

                        assemblyWs.on('open', () => {
                            console.log('✅ AssemblyAI WebSocket connected - ready for audio');
                            clientWs.send(JSON.stringify({
                                type: 'status',
                                message: '✅ Connected to speech recognition! Start speaking...'
                            }));
                        });

                        assemblyWs.on('message', (assemblyMessage) => {
                            const messageStr = assemblyMessage.toString();
                            console.log('📨 AssemblyAI message:', messageStr);

                            try {
                                const data = JSON.parse(messageStr);
                                if (data.type === 'Turn' && data.transcript) {
                                    console.log('🗣️ TRANSCRIPTION:', data.transcript);
                                    // Send transcription back to client
                                    clientWs.send(JSON.stringify({
                                        type: 'transcript',
                                        text: data.transcript
                                    }));
                                }
                            } catch (e) {
                                console.log('📨 Raw message:', messageStr);
                            }
                        });

                        assemblyWs.on('error', (error) => {
                            console.error('❌ AssemblyAI Error:', error);
                            clientWs.send(JSON.stringify({
                                type: 'error',
                                message: 'Speech recognition error'
                            }));
                        });

                        assemblyWs.on('close', () => {
                            console.log('🔌 AssemblyAI connection closed');
                        });
                    }

                    
                    if (data.type === 'stopListening') {
                        console.log('⏹️ Stopping listening session...');
                        this.cleanup(null, assemblyWs);

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
                this.cleanup(null, assemblyWs);
            });
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

    cleanup(unused, assemblyWs) {
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
            console.log('🎧 Using browser-based audio capture with 16kHz resampling');
            console.log('🤖 AssemblyAI real-time transcription enabled');
            console.log('📱 Open the URL above in your browser to start\n');
            console.log('💡 Make sure your microphone is connected and working!');
            console.log('🔧 Optimized for browser audio streaming!');
        });
    }
}

const server = new CharacterAssistantServer();
server.start();