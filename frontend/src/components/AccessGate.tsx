import { useState } from 'react'
import logo from '../assets/Sound Metrics Studio-Final-01.png'

const ACCESS_CODE = 'MYDATA26'
const STORAGE_KEY = 'ai_access_granted'

interface Props { onGranted: () => void }

export function AccessGate({ onGranted }: Props) {
  const [code, setCode] = useState('')
  const [error, setError] = useState(false)
  const [shaking, setShaking] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (code.trim().toUpperCase() === ACCESS_CODE) {
      localStorage.setItem(STORAGE_KEY, '1')
      onGranted()
    } else {
      setError(true)
      setShaking(true)
      setTimeout(() => setShaking(false), 500)
    }
  }

  return (
    <div style={{ minHeight:'100vh', background:'#1F3864', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'24px', fontFamily:"'Plus Jakarta Sans', sans-serif" }}>
      <div style={{ background:'#fff', borderRadius:'18px', padding:'48px 40px', width:'100%', maxWidth:'420px', textAlign:'center', boxShadow:'0 24px 64px rgba(0,0,0,0.3)', animation: shaking ? 'shake 0.4s ease' : undefined }}>
        <img src={logo} alt="Sound Metrics Studio" style={{ height:'48px', width:'auto', margin:'0 auto 24px', display:'block' }} />
        <div style={{ display:'inline-block', background:'#1F3864', color:'#fff', fontSize:'13px', fontWeight:700, padding:'4px 14px', borderRadius:'99px', marginBottom:'20px' }}>Artist Intelligence</div>
        <h1 style={{ fontSize:'22px', fontWeight:800, color:'#1F3864', marginBottom:'8px' }}>Private beta</h1>
        <p style={{ fontSize:'14px', color:'#5C6278', lineHeight:1.6, marginBottom:'32px' }}>This platform is currently in private testing.<br/>Enter your access code to continue.</p>
        <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
          <input type="text" value={code} onChange={e => { setCode(e.target.value); setError(false) }} placeholder="Enter access code" autoFocus autoComplete="off"
            style={{ width:'100%', padding:'13px 16px', border:`1.5px solid ${error ? '#E91E8C' : '#E1E3EA'}`, borderRadius:'10px', fontSize:'15px', fontFamily:'inherit', fontWeight:600, letterSpacing:'0.1em', textTransform:'uppercase', outline:'none', textAlign:'center', color:'#1F3864', boxSizing:'border-box' }} />
          {error && <p style={{ fontSize:'13px', color:'#E91E8C', margin:0, fontWeight:500 }}>That code isn't right. Check with your contact at Sound Metrics Studio.</p>}
          <button type="submit" style={{ width:'100%', padding:'13px', background:'#E91E8C', color:'#fff', border:'none', borderRadius:'10px', fontSize:'15px', fontWeight:700, fontFamily:'inherit', cursor:'pointer' }}>Access platform</button>
        </form>
        <p style={{ fontSize:'12px', color:'#9DA3B4', marginTop:'24px' }}>Don't have a code? <a href="mailto:hello@soundmetricsstudio.com" style={{ color:'#1F3864', fontWeight:600, textDecoration:'none' }}>Get in touch</a></p>
      </div>
      <p style={{ color:'rgba(255,255,255,0.35)', fontSize:'12px', marginTop:'32px', fontStyle:'italic' }}>Own your journey, the data was always yours.</p>
      <style>{`@keyframes shake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-8px)} 40%{transform:translateX(8px)} 60%{transform:translateX(-6px)} 80%{transform:translateX(6px)} }`}</style>
    </div>
  )
}