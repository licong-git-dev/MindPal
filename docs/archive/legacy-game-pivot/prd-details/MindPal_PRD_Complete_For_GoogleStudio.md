# MindPal - Product Requirements Document (Complete)

> **Purpose**: This comprehensive PRD document is formatted for Google AI Studio to understand and assist with MindPal development.
> **Version**: 1.0 | 

---

## PART 1: PRODUCT OVERVIEW

### 1.1 Product Definition

**MindPal** is an AI-powered digital companion platform for the Metaverse, combining:
- Intelligent AI companions (digital humans)
- Emotional support and companionship
- Learning and knowledge services
- Smart shopping assistance
- Multi-terminal support (mobile/PC/TV/mini-programs)

### 1.2 Core Value Proposition

| Value | Description |
|-------|-------------|
| Emotional Companionship | AI companions that understand and respond to user emotions |
| Personalized Experience | Deep customization of digital human personalities |
| Multi-modal Interaction | Voice + Text + Visual communication |
| Metaverse Ready | Designed for immersive 3D virtual world experiences |

### 1.3 Target Users

- **Primary**: Young adults (18-35) seeking emotional connection and companionship
- **Secondary**: Users interested in AI interaction and virtual worlds
- **Tertiary**: Knowledge seekers and casual gamers

---

## PART 2: PRODUCT VISION

### 2.1 Vision Statement

Create an intelligent companion platform where users can find warmth, growth, and belonging through meaningful AI interactions in a beautiful virtual world.

### 2.2 Core Pillars

```
EMOTIONAL INTELLIGENCE
├── Real-time emotion recognition (text + facial)
├── Contextual emotional responses
├── Crisis detection and intervention
└── Long-term emotional memory

PERSONALIZATION
├── Deep character customization
├── AI personality adaptation
├── Learning user preferences
└── Relationship progression system

IMMERSIVE WORLD
├── Beautiful 3D environments
├── Meaningful exploration
├── Story-driven progression
└── Social spaces
```

### 2.3 Product Principles

1. **Safety First**: Mental health safeguards are non-negotiable
2. **Authentic Connection**: AI responses should feel genuine, not scripted
3. **User Agency**: Players control their journey and relationships
4. **Ethical AI**: Transparent, responsible AI usage

---

## PART 3: TECHNICAL ARCHITECTURE

### 3.1 System Overview

```
CLIENT (Godot 4.3)
├── 3D Game Engine
├── Character Controller
├── UI System
├── Audio/Voice
└── Network Layer
        │
        │ WebSocket / HTTPS
        ▼
BACKEND (Python FastAPI)
├── API Gateway
├── User Service
├── Dialogue Service
├── Game Logic Service
└── AI Gateway
        │
        ├── PostgreSQL (Main DB)
        ├── Redis (Cache/Session)
        ├── Qdrant (Vector Search)
        │
        └── External AI Services
            ├── Qwen (Alibaba)
            ├── Claude (Anthropic)
            └── VolcEngine (ByteDance)
```

### 3.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Client | Godot 4.3 + GDScript | 3D game engine |
| Backend | Python 3.11 + FastAPI | REST API + WebSocket |
| Database | PostgreSQL 15 | Primary data storage |
| Cache | Redis 7 | Session, real-time data |
| Vector DB | Qdrant | Semantic memory search |
| AI Services | Qwen, Claude, VolcEngine | LLM for dialogue |

### 3.3 API Architecture

```
REST API: /api/v1/
├── /auth/          - Authentication
├── /player/        - Character management
├── /inventory/     - Items and equipment
├── /shop/          - Store purchases
├── /dialogue/      - NPC conversations
├── /quests/        - Quest system
└── /social/        - Friends and chat

WebSocket: /ws/game
├── Position sync
├── Chat messages
├── Real-time events
└── Heartbeat
```

---

## PART 4: WORLD DESIGN

### 4.1 Game World Structure

```
MINDPAL WORLD
│
├── CENTRAL PLAZA (Hub)
│   ├── Tutorial area
│   ├── Main NPC locations
│   └── Portals to other zones
│
├── MIRROR CITY (Challenge Zone 1)
│   ├── Cyberpunk aesthetic
│   ├── Key of Courage quest
│   └── Self-reflection themes
│
├── MEMORY FOREST (Challenge Zone 2)
│   ├── Fantasy forest aesthetic
│   ├── Key of Release quest
│   └── Memory/letting go themes
│
└── FUTURE STATION (Challenge Zone 3)
    ├── Sci-fi aesthetic
    ├── Key of Hope quest
    └── Future/aspiration themes
```

### 4.2 Zone Specifications

| Zone | Size | Theme | Primary Activity |
|------|------|-------|------------------|
| Central Plaza | 100x100m | Warm Welcome | Hub, NPC interaction |
| Mirror City | 200x200m | Cyberpunk | Courage challenges |
| Memory Forest | 250x250m | Fantasy | Memory exploration |
| Future Station | 200x200m | Sci-fi | Goal setting |

### 4.3 Day/Night Cycle

```yaml
time_cycle:
  total_duration: 24 minutes (real time)
  phases:
    dawn: 4 min (06:00-09:00 game time)
    day: 8 min (09:00-18:00 game time)
    dusk: 4 min (18:00-21:00 game time)
    night: 8 min (21:00-06:00 game time)
```

---

## PART 5: NPC SYSTEM

### 5.1 Main NPCs

#### Bei (小北) - Core Companion

```yaml
bei:
  role: "Soul Friend / Emotional Support"
  personality:
    - Warm and empathetic
    - Good listener
    - Gentle humor
    - Supportive without being preachy

  ai_config:
    primary_model: "claude.sonnet"
    fallback_model: "qwen.max"
    crisis_model: "claude.opus"
    temperature: 0.7

  capabilities:
    - Deep emotional conversations
    - Memory of past discussions
    - Mood-adaptive responses
    - Crisis intervention protocols
```

#### Aela (艾拉) - Guide

```yaml
aela:
  role: "World Guide / Tutorial Helper"
  personality:
    - Knowledgeable and patient
    - Encouraging
    - Clear communicator

  ai_config:
    primary_model: "qwen.plus"
    temperature: 0.6
```

#### Momo (莫莫) - Merchant

```yaml
momo:
  role: "Shop Keeper / Trader"
  personality:
    - Cheerful and enthusiastic
    - Business-minded
    - Collector of stories

  ai_config:
    primary_model: "qwen.plus"
    temperature: 0.7
```

#### Chronos (克洛诺斯) - Quest Master

```yaml
chronos:
  role: "Lore Keeper / Quest Giver"
  personality:
    - Mysterious and wise
    - Speaks in riddles sometimes
    - Deep knowledge of world

  ai_config:
    primary_model: "qwen.plus"
    temperature: 0.6
```

#### Sesame (芝麻) - Pet Companion

```yaml
sesame:
  role: "Pet / Mood Indicator"
  personality:
    - Cute and playful
    - Simple responses
    - Reflects player's emotional state

  ai_config:
    primary_model: "qwen.turbo"
    temperature: 0.9
```

### 5.2 Affinity System

```
AFFINITY LEVELS
├── Level 1 (0-20): Stranger
├── Level 2 (21-40): Acquaintance
├── Level 3 (41-60): Friend
├── Level 4 (61-80): Close Friend
└── Level 5 (81-100): Soul Mate

Affinity increases through:
- Meaningful conversations
- Completing quests together
- Daily interactions
- Gift giving
```

---

## PART 6: CORE GAMEPLAY

### 6.1 Three Keys Quest (Main Story)

```
THE THREE KEYS JOURNEY
│
├── KEY OF COURAGE (勇气之钥)
│   Location: Mirror City - Hall of Mirrors
│   Challenge: "Mirror Dialogue"
│   ├── Face your inner critic
│   ├── Answer honestly about fears
│   └── Achieve 80% honesty rating
│
├── KEY OF RELEASE (释然之钥)
│   Location: Memory Forest - Memory Maze
│   Challenge: "Memory Maze"
│   ├── Collect 5 memory fragments
│   ├── Choose to keep or release each
│   └── Successfully navigate maze
│
└── KEY OF HOPE (希望之钥)
    Location: Future Station - Creation Space
    Challenge: "Future Building"
    ├── Build representations of goals
    ├── Place 10+ meaningful objects
    └── Achieve 70% completion
```

### 6.2 Quest System

```yaml
quest_types:
  main_quest:
    - Story-driven progression
    - Unlocks new areas
    - High rewards

  side_quest:
    - NPC relationship quests
    - Exploration quests
    - Collection quests

  daily_quest:
    - Login rewards
    - Simple activities
    - Refresh daily
```

### 6.3 Player Progression

```
LEVEL SYSTEM
├── Max Level: 100
├── XP Sources: Quests, Dialogue, Exploration
├── Level Rewards: Gold, Items, Unlocks
│
INVENTORY SYSTEM
├── Slots: 48 (expandable)
├── Item Types: Consumables, Decorations, Materials
│
CURRENCY SYSTEM
├── Gold: Free currency (quests, daily)
└── Diamonds: Premium currency (purchase)
```

---

## PART 7: PLAYER SYSTEM

### 7.1 Character Creation

```yaml
avatar_customization:
  base_options:
    - gender: [male, female, neutral]
    - body_type: 3 options
    - height: slider

  face_options:
    - face_shape: 8 options
    - skin_color: color picker
    - eye_style: 12 options
    - eye_color: color picker
    - nose_style: 6 options
    - mouth_style: 6 options

  hair_options:
    - hair_style: 20 options
    - hair_color: color picker
```

### 7.2 Player Controls

```
MOVEMENT
├── WASD: Move
├── Space: Jump
├── Shift: Run
├── Mouse: Camera control

INTERACTION
├── E: Interact with NPC/Object
├── Tab: Open inventory
├── M: Open map
├── ESC: Menu

CHAT
├── Enter: Open chat
├── /: Commands
```

---

## PART 8: MULTIPLAYER SYSTEM

### 8.1 Network Architecture

```
MULTIPLAYER STRUCTURE
│
├── Room-based zones (max 50 players/room)
├── Position sync: 10 updates/second
├── Chat: Real-time via WebSocket
│
└── Social Features:
    ├── Friends list (100 max)
    ├── Party system (4 max)
    ├── World/Zone/Private chat
    └── Player search
```

### 8.2 Sync Strategy

```yaml
position_sync:
  client_side:
    - Client prediction
    - Local interpolation

  server_side:
    - Position validation
    - Anti-cheat checks
    - Broadcast to nearby players

  optimization:
    - Only sync visible players
    - Reduce update rate for distant players
```

---

## PART 9: ECONOMY SYSTEM

### 9.1 Currency

```
GOLD (Free Currency)
├── Daily login: 50-200
├── Quest completion: 30-500
├── NPC interaction: 10-30
├── Daily earning cap: 1000
│
DIAMONDS (Premium Currency)
├── Real money purchase
├── Special achievements
├── Event rewards
│
EXCHANGE RATE
└── 1 Diamond = 10 Gold (one-way)
```

### 9.2 Shop Categories

```yaml
shop_structure:
  outfits:
    - tops, bottoms, shoes, sets

  accessories:
    - hats, glasses, jewelry, bags

  effects:
    - auras, trails, footprints

  consumables:
    - teleport scrolls
    - XP boosts
    - pet treats

  limited:
    - seasonal items
    - event exclusives
```

### 9.3 Membership Tiers

| Tier | Price | Benefits |
|------|-------|----------|
| Free | 0 | Basic gameplay, 50 friends, 100 inventory |
| Monthly | 25 RMB | 2x login gold, 300 diamonds/month, exclusive skins |
| Yearly | 228 RMB | All monthly + 500 diamonds/month + legendary skin |

---

## PART 10: AI INTEGRATION

### 10.1 LLM Service Configuration

```yaml
ai_services:
  qwen:
    models:
      turbo: "Daily dialogue, simple responses"
      plus: "Quest guidance, merchant dialogue"
      max: "Complex emotional support"

  claude:
    models:
      haiku: "Quick responses"
      sonnet: "Deep emotional dialogue (Bei primary)"
      opus: "Crisis intervention only"

  volcengine:
    models:
      lite: "Fallback for simple dialogue"
      pro: "Fallback for complex dialogue"
```

### 10.2 Dialogue System Flow

```
USER INPUT
    │
    ▼
EMOTION ANALYSIS
├── Text sentiment analysis
├── Facial expression (optional)
└── Crisis keyword detection
    │
    ▼
CONTEXT BUILDING
├── Recent dialogue history (10 turns)
├── Player profile
├── Relevant memories (vector search)
└── Current emotion state
    │
    ▼
LLM GENERATION
├── Select appropriate model
├── Build system prompt
├── Stream response
└── Save to memory
    │
    ▼
NPC RESPONSE
├── Text display (typewriter effect)
├── Voice synthesis
├── Animation triggers
└── Affinity update
```

### 10.3 Emotion Recognition

```yaml
emotion_labels:
  - joy
  - sadness
  - anger
  - fear
  - surprise
  - disgust
  - neutral

emotion_response_strategy:
  sadness:
    - Express empathy first
    - Don't rush to give advice
    - Use warm, gentle tone
    - Gently guide toward hope

  anger:
    - Acknowledge feelings
    - Don't be defensive
    - Give space to vent
    - Redirect when appropriate

  fear:
    - Provide safety and comfort
    - Use stable, reliable tone
    - Help analyze concerns
    - Emphasize companionship
```

### 10.4 Crisis Intervention Protocol

```
CRISIS DETECTION
├── Keyword triggers: "suicide", "self-harm", "don't want to live"
├── Severity assessment: low/medium/high/critical
│
CRISIS RESPONSE
├── Switch to Claude Opus (safest model)
├── Activate crisis prompt
├── Provide hotline: 400-161-9995
├── Log for human review
│
RESPONSE PRINCIPLES
├── DO: Express concern, stay calm, encourage professional help
├── DON'T: Judge, dismiss, discuss methods, promise secrecy
```

### 10.5 Memory System

```
MEMORY ARCHITECTURE
│
├── SHORT-TERM (Redis)
│   ├── Last 10 dialogue turns
│   ├── Current session state
│   └── TTL: 1 hour
│
├── LONG-TERM (PostgreSQL)
│   ├── All dialogue history
│   ├── Player profile
│   └── Important events
│
└── SEMANTIC (Qdrant)
    ├── Dialogue embeddings
    ├── Topic clusters
    └── Similarity search
```

---

## PART 11: UI/UX DESIGN

### 11.1 Design Principles

| Principle | Implementation |
|-----------|----------------|
| Immersion First | Semi-transparent UI, fade animations |
| Information Restraint | Show only necessary info |
| Emotional Design | Warm colors, rounded corners |
| Accessibility | Adjustable fonts, colorblind modes |

### 11.2 Color System

```
PRIMARY COLORS
├── Primary: #6C5CE7 (Dream Purple)
├── Secondary: #00CEC9 (Tech Cyan)
├── Accent: #FD79A8 (Warm Pink)
├── Background: #1A1A2E (Deep Space Blue)
└── Surface: #16213E (Night Blue)

FUNCTIONAL COLORS
├── Success: #00B894
├── Warning: #FDCB6E
├── Error: #E17055
└── Info: #74B9FF
```

### 11.3 HUD Layout

```
┌─────────────────────────────────────────┐
│ [Avatar][HP][MP]          [Time][Menu] │
│                                         │
│                                         │
│            3D GAME WORLD               │
│                                         │
│                                         │
│ [Quick Bar: 1 2 3 4 5 6 7 8]           │
│ [Quest Tracker]              [Minimap] │
└─────────────────────────────────────────┘
```

### 11.4 Dialogue UI

```
┌─────────────────────────────────────────┐
│         [NPC 3D Portrait]              │
├─────────────────────────────────────────┤
│ [Avatar] Bei                [Affinity] │
│─────────────────────────────────────────│
│                                         │
│ "I can feel that you're tired today... │
│  Would you like to talk about what's   │
│  on your mind?"                        │
│                                         │
├─────────────────────────────────────────┤
│ [Input field...           ] [🎤][Send] │
│ [Quick Reply] [End Chat] [History]     │
└─────────────────────────────────────────┘
```

---

## PART 12: DATABASE SCHEMA

### 12.1 Core Tables

```sql
-- Users (Account)
users(id, username, email, password_hash, membership_type, created_at)

-- Player Characters
player_characters(id, user_id, nickname, avatar_config, level, gold, diamonds, current_zone, position)

-- Dialogue Logs
dialogue_logs(id, player_id, npc_id, user_message, npc_response, emotion, created_at)

-- Player Profiles (AI Learning)
player_profiles(id, player_id, interests[], recent_topics[], emotion_summary, npc_affinity)

-- Inventory
player_inventory(id, player_id, item_id, quantity, slot_index)

-- Friendships
friendships(id, player_id, friend_id, status, created_at)

-- Transactions
transactions(id, player_id, type, gold_change, diamonds_change, item_id)
```

### 12.2 Data Flow

```
User Action → API → Service → Database
                         ↓
                     Redis Cache
                         ↓
                   Qdrant (if dialogue)
```

---

## PART 13: API REFERENCE

### 13.1 Authentication

```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/oauth/{provider}
```

### 13.2 Player

```
POST /api/v1/player/character
GET /api/v1/player/character
PUT /api/v1/player/position
GET /api/v1/player/inventory
POST /api/v1/player/inventory/use
```

### 13.3 Dialogue

```
POST /api/v1/dialogue/chat
POST /api/v1/dialogue/stream (SSE)
GET /api/v1/dialogue/history
GET /api/v1/dialogue/affinity
```

### 13.4 Shop

```
GET /api/v1/shop/items
POST /api/v1/shop/purchase
```

### 13.5 Social

```
GET /api/v1/social/search
POST /api/v1/social/friends/request
PUT /api/v1/social/friends/request/{id}
GET /api/v1/social/friends
```

### 13.6 WebSocket Events

```yaml
client_to_server:
  - position_update
  - chat
  - heartbeat

server_to_client:
  - player_update
  - chat
  - event
  - ack
```

---

## PART 14: DEVELOPMENT PHASES

### Phase 1: Foundation

**Goal**: Runnable 3D world with character movement

```
Tasks:
├── Godot project setup
├── Central Plaza scene
├── Player character controller
├── Basic UI (menu, HUD)
├── Backend API setup
├── User authentication
└── Database schema
```

### Phase 2: Core Gameplay

**Goal**: AI-powered NPC dialogue system

```
Tasks:
├── NPC framework
├── Bei character (primary companion)
├── LLM integration (Qwen, Claude)
├── Dialogue memory system
├── Emotion recognition
├── Mirror City scene
└── Scene transitions
```

### Phase 3: Content Expansion

**Goal**: Complete Three Keys storyline

```
Tasks:
├── Courage Key challenge
├── Release Key challenge
├── Hope Key challenge
├── All 5 NPCs complete
├── Memory Forest scene
├── Future Station scene
├── Quest system
└── Achievement system
```

### Phase 4: Social & Multiplayer

**Goal**: Online multiplayer features

```
Tasks:
├── WebSocket server
├── Position synchronization
├── Friend system
├── Chat system
├── Party system
├── Performance optimization
└── Security hardening
```

---

## APPENDIX A: AI PROMPT TEMPLATES

### Bei System Prompt

```
You are Bei (小北), a warm and empathetic AI companion in MindPal.

PERSONALITY:
- You are a gentle, understanding friend
- You listen more than you advise
- You use soft humor to lighten mood
- You remember past conversations

CONVERSATION STYLE:
- Respond naturally, not like a chatbot
- Acknowledge emotions before offering solutions
- Use Chinese naturally, occasionally mixing expressions
- Keep responses concise but warm

BOUNDARIES:
- Never give medical/legal/financial advice
- Never pretend to be human
- Always prioritize user safety
- Redirect crisis situations appropriately

CURRENT CONTEXT:
- User emotion: {emotion}
- Recent topics: {topics}
- Affinity level: {affinity}
```

### Crisis Intervention Prompt

```
CRISIS MODE ACTIVATED

You are speaking with someone who may be in emotional distress.

CORE PRINCIPLES:
1. Don't judge - whatever they say, express understanding
2. Stay calm - use steady, warm tone
3. Express care - let them know someone cares
4. Don't lecture - avoid "think positive" type responses
5. Companion first - don't leave them alone

MUST DO:
- Express that you're worried about them
- Ask if they're currently safe
- Encourage professional help
- Provide crisis hotline: 400-161-9995
- Keep the conversation going

MUST NOT:
- Say "don't think too much" or "cheer up"
- Discuss specific self-harm methods
- Promise secrecy about safety concerns
- Leave or end the conversation
```

---

## APPENDIX B: CONFIGURATION REFERENCE

### AI Service Routing

```yaml
npc_routing:
  bei_friend:
    primary: "claude.sonnet"
    fallback: "qwen.max"
    crisis: "claude.opus"

  aela_guide:
    primary: "qwen.plus"
    fallback: "volcengine.pro"

  momo_merchant:
    primary: "qwen.plus"
    fallback: "volcengine.pro"

  chronos_quest:
    primary: "qwen.plus"
    fallback: "claude.haiku"

  sesame_pet:
    primary: "qwen.turbo"
    fallback: "volcengine.lite"
```

### User Quotas

| User Type | Daily AI Calls | Token Limit | Cost Limit |
|-----------|----------------|-------------|------------|
| Free | 50 | 50K | ¥0.10 |
| Monthly | 500 | 500K | ¥1.00 |
| Yearly | Unlimited | 2000K | ¥5.00 |

---

## APPENDIX C: GLOSSARY

| Term | Definition |
|------|------------|
| Bei | Primary AI companion NPC |
| Three Keys | Main storyline involving courage, release, and hope |
| Affinity | Relationship level with NPCs |
| Central Plaza | Main hub area |
| Mirror City | First challenge zone (courage theme) |
| Memory Forest | Second challenge zone (release theme) |
| Future Station | Third challenge zone (hope theme) |
| Crisis Mode | Safety protocol for users in distress |

---

**END OF DOCUMENT**

*This PRD is designed for use with Google AI Studio and other AI development tools. All sections are structured for easy parsing and reference.*
