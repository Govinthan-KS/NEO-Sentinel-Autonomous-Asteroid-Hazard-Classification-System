import { toast } from 'sonner';

const defaultStyle = {
  background: 'rgba(238, 242, 246, 0.85)',
  backdropFilter: 'blur(12px)',
  color: '#0f172a',
};

export const showSuccessToast = (title: string, description?: string) => {
  toast.success(title, {
    description,
    style: {
      ...defaultStyle,
      borderLeft: '4px solid #10B981',
      boxShadow: '0 0 20px rgba(16, 185, 129, 0.1)',
      borderTop: '1px solid rgba(255, 255, 255, 0.5)',
      borderRight: '1px solid rgba(255, 255, 255, 0.5)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.5)',
    },
    classNames: { title: '!text-[#10B981]' },
  });
};

export const showErrorToast = (title: string, description?: string) => {
  toast.error(title, {
    description,
    style: {
      ...defaultStyle,
      borderLeft: '4px solid #EF4444',
      boxShadow: '0 0 20px rgba(239, 68, 68, 0.1)',
      borderTop: '1px solid rgba(255, 255, 255, 0.5)',
      borderRight: '1px solid rgba(255, 255, 255, 0.5)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.5)',
    },
    classNames: { title: '!text-[#EF4444]' },
  });
};

export const showWarningToast = (title: string, description?: string) => {
  toast.warning(title, {
    description,
    style: {
      ...defaultStyle,
      borderLeft: '4px solid #F59E0B',
      boxShadow: '0 0 20px rgba(245, 158, 11, 0.1)',
      borderTop: '1px solid rgba(255, 255, 255, 0.5)',
      borderRight: '1px solid rgba(255, 255, 255, 0.5)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.5)',
    },
    classNames: { title: '!text-[#F59E0B]' },
  });
};

export const showInfoToast = (title: string, description?: string) => {
  toast.info(title, {
    description,
    style: {
      ...defaultStyle,
      borderLeft: '4px solid #3B82F6',
      boxShadow: '0 0 20px rgba(59, 130, 246, 0.1)',
      borderTop: '1px solid rgba(255, 255, 255, 0.5)',
      borderRight: '1px solid rgba(255, 255, 255, 0.5)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.5)',
    },
    classNames: { title: '!text-[#3B82F6]' },
  });
};

// Auth Stubs for next step
export const showAuthSuccessToast = () => {
  showSuccessToast('Authentication Successful', 'Secure session established.');
};

export const showAuthErrorToast = () => {
  showErrorToast('Authentication Failed', 'Invalid credentials or session expired.');
};

export const handleApiError = (error: any) => {
  const status = error?.response?.status;
  if (status === 401) {
    showErrorToast('Unauthorized', 'Please log in to perform this action.');
  } else if (status === 429) {
    showErrorToast('Rate Limit Exceeded', 'Too many requests. Please try again later.');
  } else if (status === 500) {
    showErrorToast('Server Error', 'An unexpected error occurred on the server.');
  } else {
    showErrorToast('API Error', error?.message || 'Failed to communicate with the server.');
  }
};
