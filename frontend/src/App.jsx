import { useState } from 'react'
import './App.css'

function App() {
  const [input, setInput] = useState('')
  const [response, setResponse] = useState('')
  const [audioFile, setAudioFile] = useState(null)

  const handleTextSubmit = async () => {
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: input }),
    })

    const data = await res.json()
    setResponse(data.answer)
  }

  const handleFileUpload = async () => {
    if (!audioFile) return alert('파일을 선택해주세요!')

    const formData = new FormData()
    formData.append('file', audioFile)

    const res = await fetch('http://localhost:8000/summarize-audio', {
      method: 'POST',
      body: formData,
    })

    const data = await res.json()
    setResponse(data.summary)
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>🩺 MeDot</h1>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="질문을 입력하세요"
        style={{ width: '300px', marginRight: '1rem' }}
      />
      <button onClick={handleTextSubmit}>보내기</button>

      <hr style={{ margin: '2rem 0' }} />

      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setAudioFile(e.target.files[0])}
      />
      <button onClick={handleFileUpload} style={{ marginLeft: '1rem' }}>
        녹음 파일 요약
      </button>

      <div style={{ marginTop: '2rem' }}>
        <strong>🧠 응답 결과:</strong>
        <p>{response}</p>
      </div>
    </div>
  )
}

export default App
