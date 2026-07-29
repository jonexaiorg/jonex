import { useTranslation } from 'react-i18next';
import FeedbackList from './FeedbackList';

interface LikeTabProps {
  kbId: string;
}

export default function LikeTab({ kbId }: LikeTabProps) {
  const { t } = useTranslation();
  return <FeedbackList kbId={kbId} feedbackType="like" title={t('compile.feedback.likeTitle')} />;
}
