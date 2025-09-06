# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Personal Stylist AI

## [1.0.0] - 2024-12-19

### Added
- Multi-angle body analysis with privacy protection
- AI-powered clothing recognition and categorization
- Weather-aware outfit recommendations
- Shopping intelligence and fit prediction
- Multi-user family support
- Mobile-optimized Streamlit interface
- Complete local processing (no external services)
- Docker containerization for easy deployment
- Unraid Community Applications integration
- Automated CI/CD pipeline with GitHub Actions

### Features
- **Privacy-First Design**: All AI processing happens locally
- **Smart Body Analysis**: Multi-angle photo processing with immediate anonymization
- **Intelligent Clothing Recognition**: Automatic analysis of colors, patterns, and styles
- **Weather Integration**: Daily outfit recommendations based on local weather
- **Shopping Assistant**: Analyze products before buying, predict fit
- **Family Support**: Multiple user profiles with individual preferences
- **Mobile Optimized**: Works great on phones and tablets

### Security
- Privacy-first design with local-only processing
- Anonymous body measurement conversion
- Encrypted local data storage
- No external service dependencies

### Technical
- Streamlit web interface
- MediaPipe for pose estimation
- OpenCV for image processing
- SQLite database for local storage
- Docker containerization
- Multi-platform support (AMD64, ARM64)

[Unreleased]: https://github.com/neil-zielsdorf/personal-stylist-ai/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/neil-zielsdorf/personal-stylist-ai/releases/tag/v1.0.0