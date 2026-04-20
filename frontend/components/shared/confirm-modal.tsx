import { Button, Modal, Spinner } from "@heroui/react";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  isLoading?: boolean;
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  isLoading,
}: ConfirmModalProps) {
  return (
    <Modal.Root
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Modal.Backdrop isDismissable>
        <Modal.Container>
          <Modal.Dialog>
            <Modal.Header>
              <Modal.Heading>{title}</Modal.Heading>
            </Modal.Header>
            <Modal.Body>
              <p className="text-sm">{message}</p>
            </Modal.Body>
            <Modal.Footer className="gap-2">
              <Button variant="ghost" onPress={onClose}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onPress={onConfirm}
                isDisabled={isLoading}
              >
                {isLoading ? <Spinner size="sm" /> : "Confirm"}
              </Button>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal.Root>
  );
}
