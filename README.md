# Leurs - Discord Balance Bot

A feature-rich Discord bot designed to enhance your server experience with economy, moderation, music integration, and utility commands.

![Discord Bot](https://img.shields.io/badge/Discord-Bot-7289da?style=for-the-badge&logo=discord&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**[docs.leurs.ch](https://docs.leurs.ch)**

## 🌟 Features

### 💰 Economy System
- Virtual currency management with wallet and bank accounts
- Betting and gambling mechanics
- Job market with multiple career paths
- Daily rewards and income opportunities

### 🛡️ Advanced Moderation
- Comprehensive user management (ban, kick, mute, jail)
- Warning system with history tracking
- Smart message deletion with cached search
- Role management and automatic role restoration
- Nickname management with history

### 🎵 Last.fm Integration
- Real-time music tracking and display
- Server-wide now playing overview
- User music statistics and profiles
- Scrobble counts and listening history

### 📊 Leveling System
- XP-based progression system
- Server leaderboards
- Visual progress bars
- Level-based rewards

### ⚙️ Administrative Tools
- Automated role saving and restoration
- Message caching and advanced search
- Custom embed creation
- Auto-reactions and reaction roles
- Bulk message management

### 🎯 Utility Commands
- Birthday tracking and reminders
- Timezone management
- Custom quote generation
- Random lyric display
- Information and help commands

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/IM23d/discord-balance-bot.git
   cd discord-balance-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file
   - Add your Discord bot token and other required API keys

4. **Run the bot**
   ```bash
   python main.py
   ```

## 📚 Documentation

For detailed command documentation, setup guides, and configuration options, visit our comprehensive documentation website:

**[📖 docs.leurs.ch](https://docs.leurs.ch)**

The documentation includes every command alongside how to use it.


## 🎮 Command Preview

| Category | Examples |
|----------|----------|
| **Economy** | `-balance`, `-beg`, `-gamble`, `-deposit` |
| **Jobs** | `-jobs`, `-work`, `-buyjob`, `-myjobs` |
| **Moderation** | `-warn`, `-ban`, `-mute`, `-jail` |
| **Music** | `-np`, `-lastfm`, `-servernowplaying` |
| **Levels** | `-rank`, `-leveltop`, `-setlevel` |
| **Utility** | `-info`, `-birthday`, `-timezone` |

---

## 🚀 Features

- **💰 Economy System**: Virtual currency, gambling, jobs, and daily rewards
- **🛡️ Advanced Moderation**: Comprehensive user management with warnings and role automation
- **🎵 Last.fm Integration**: Real-time music tracking and server-wide now playing
- **📊 Leveling System**: XP-based progression with leaderboards and rewards
- **⚙️ Admin Tools**: Custom embeds, reaction roles, and bulk management
- **🎯 Utilities**: Birthday tracking, timezone management, and quotes

## 📦 Installation

### Using Docker (Recommended)

**1. Create your configuration:**
```bash
# Clone the repository
git clone https://github.com/IM23d/leurs.git
cd leurs

# Copy and configure environment file
cp .env.template .env
# Edit .env with your bot token and API keys
```

**2. Create a `compose.yml` file:**
```yaml
services:
  leurs:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: leurs-bot
    env_file:
      - .env
    restart: unless-stopped
```

**3. Start the bot:**
```bash
docker compose up -d
```

### Manual Installation

```bash
# Clone and setup
git clone https://github.com/IM23d/leurs.git
cd leurs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your credentials

# Run the bot
python main.py
```

## ⚙️ Configuration

Configure your `.env` file with the following:

```properties
# Discord bot token (Required)
DISCORD_TOKEN=your_discord_bot_token

# Last.fm API (Optional - for music features)
LAST_FM_KEY=your_lastfm_api_key

# Google Custom Search API (Optional - for image search)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id

# DeepSeek API (Optional - for AI features)
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 🎮 Command Categories

| Category | Examples | Description |
|----------|----------|-------------|
| **Economy** | `-balance`, `-work`, `-gamble` | Manage virtual currency and jobs |
| **Moderation** | `-warn`, `-ban`, `-mute` | Keep your server organized |
| **Music** | `-np`, `-lastfm` | Share what you're listening to |
| **Levels** | `-rank`, `-leveltop` | Track your server progression |
| **Utility** | `-info`, `-birthday` | Helpful server tools |

For complete command documentation, visit **[docs.leurs.ch](https://docs.leurs.ch)**

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👥 Team

- **[@bettercallmilan](https://github.com/bettercallmilan)** - Developer
- **[@FlorianRuby](https://github.com/reazndev)** - Developer
- **[@seakyy](https://github.com/seakyy)** - Contributor
- **[@lhilfiker](https://github.com/lhilfiker)** - Pull Request Master

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Support the Project

If Leurs has enhanced your Discord server experience, please consider:
- ⭐ **Starring this repository** to show your support
- 🐛 **Reporting bugs** to help us improve
- 💡 **Suggesting features** for future updates
- 🤝 **Contributing code** to make Leurs even better

## 🔗 Links

- **Documentation**: [docs.leurs.ch](https://docs.leurs.ch)
- **Issues**: [GitHub Issues](https://github.com/IM23d/leurs/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/IM23d/leurs/pulls)

---


<p align="center">Made with ❤️ by the <strong>Leurs Team</strong></p>
