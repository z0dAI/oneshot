interface GoogleCredentialResponse {
  credential: string
  select_by: string
}

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string
    callback: (response: GoogleCredentialResponse) => void
    nonce?: string
    use_fedcm_for_prompt?: boolean
    auto_select?: boolean
  }) => void
  prompt: (notification?: (notification: { getMomentType: () => string }) => void) => void
  renderButton: (
    element: HTMLElement,
    config: { theme?: string; size?: string; text?: string; width?: number }
  ) => void
}

declare const google: {
  accounts: {
    id: GoogleAccountsId
  }
}
