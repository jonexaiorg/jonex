import { useTranslation } from 'react-i18next';
import FeedbackList from './FeedbackList';

interface DislikeTabProps {
  kbId: string;
}

export default function DislikeTab({ kbId }: DislikeTabProps) {
  const { t } = useTranslation();
  return <FeedbackList kbId={kbId} feedbackType="dislike" title={t('compile.feedback.dislikeTitle')} />;
}
