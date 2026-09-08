import { useState } from 'react'
import logo from '../assets/Sound Metrics Studio-Final-01.png'

interface Props {
  onBack: () => void
  onSwitchToSignIn: () => void
  onSignUp: () => void
}

// Minimal Google icon SVG — matches auth mockup
function GoogleIcon() {
  return (
    <svg className="auth-google-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

export function SignUpPage({ onBack, onSwitchToSignIn, onSignUp }: Props) {
  const [showPassword, setShowPassword] = useState(false)

  return (
    <>
      {/* Reuse the global nav bar background */}
      <nav id="nav-bar">
        <div className="nav-left" onClick={onBack}>
          <img src={logo} alt="Sound Metrics Studio" className="nav-logo-img" />
          <div className="nav-wordmark">
            <span className="nav-wordmark-title">Artist Intelligence</span>
            <span className="nav-wordmark-sub">Powered by Sound Metrics Studio</span>
          </div>
        </div>
      </nav>

      <div id="auth-page">
        {/* Back link */}
        <button className="auth-back" onClick={onBack} aria-label="Back to search">
          ← Back to search
        </button>

        <div className="auth-card">

          {/* Logo row */}
          <div className="auth-logo-row">
            <div className="auth-ai-badge">AI</div>
            <img src={logo} alt="Sound Metrics Studio" className="auth-logo-img" />
          </div>

          {/* Heading */}
          <h1 className="auth-heading">Create your account</h1>
          <p className="auth-sub">
            Create your free account to save searches, build your profile, and
            unlock Pro features when they launch. No card required.
          </p>

          {/* Promo info box */}
          <div className="auth-promo-box">
            <span className="auth-promo-icon">🎵</span>
            <span>
              Public insights are always free. Your free account saves your
              searches and puts you first in line for Pro. Pro unlocks private
              data uploads, your full Artist Insights Report, and a strategy
              session with the SMS team — founding artist pricing coming soon.
            </span>
          </div>

          {/* Google */}
          <button
            className="auth-google-btn"
            onClick={onSignUp}
            type="button"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          {/* Divider */}
          <div className="divider" style={{ marginBottom: '20px' }}>
            or sign up with email
          </div>

          {/* Form */}
          <form
            className="auth-form"
            onSubmit={e => { e.preventDefault(); onSignUp() }}
          >
            <div className="form-group">
              <label className="form-label" htmlFor="signup-name">Your name</label>
              <input
                id="signup-name"
                className="form-input"
                type="text"
                placeholder="Your name"
                autoComplete="name"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="signup-artist">
                Artist or project name used in your reports
              </label>
              <input
                id="signup-artist"
                className="form-input"
                type="text"
                placeholder="Artist or project name"
              />
              <span className="form-hint">
                This is how your data and reports will be labelled.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="signup-email">Email address</label>
              <input
                id="signup-email"
                className="form-input"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="signup-password">Password</label>
              <div className="input-password-wrap">
                <input
                  id="signup-password"
                  className="form-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="input-password-toggle"
                  onClick={() => setShowPassword(p => !p)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            {/* Promo code */}
            <div className="auth-promo-row">
              <div className="auth-promo-label-row">
                <label className="form-label" htmlFor="signup-promo">
                  Promo / founding artist code
                </label>
                <span className="auth-optional">Optional</span>
              </div>
              <input
                id="signup-promo"
                className="form-input"
                type="text"
                placeholder="e.g. FOUNDING100"
                autoComplete="off"
              />
              <span className="form-hint">
                Have a code from Sound Metrics Studio or Crescendo? Enter it here.
              </span>
            </div>

            {/* Terms */}
            <p className="auth-terms">
              By creating an account you agree to our{' '}
              <a href="#">Terms of Use</a> and{' '}
              <a href="#">Privacy Policy</a>. Your uploaded data is stored
              securely and never shared with third parties.
            </p>

            <button
              type="submit"
              className="btn btn-primary btn-full btn-lg"
            >
              Create free account
            </button>

            <p className="auth-switch">
              Already have an account?{' '}
              <button
                type="button"
                className="auth-switch-link"
                onClick={onSwitchToSignIn}
              >
                Sign in
              </button>
            </p>
          </form>

        </div>
      </div>
    </>
  )
}
