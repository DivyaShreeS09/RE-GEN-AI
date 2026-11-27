import { Component } from 'react'

export default class AnalysisErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (!this.state.failed) return this.props.children

    return (
      <section role="alert" className="glass-card max-w-2xl mx-auto my-10 p-6">
        <h2 className="text-lg font-semibold text-white">RE:GEN AI could not display this view</h2>
        <p className="mt-2 text-sm text-slate-300">
          {this.props.analysis ? 'Retry displaying the results or start a new analysis.' : 'Retry opening the application.'}
        </p>
        <button type="button" className="mt-4 rounded bg-cyan-900 px-4 py-2 text-white"
          onClick={() => this.setState({ failed: false })}>
          {this.props.analysis ? 'Retry displaying results' : 'Retry opening RE:GEN AI'}
        </button>
      </section>
    )
  }
}
