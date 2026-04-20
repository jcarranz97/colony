"use client";
import { useState } from "react";
import { Formik } from "formik";
import {
  Button,
  FieldError,
  Input,
  Label,
  ListBox,
  Modal,
  Select,
  Spinner,
  TextField,
} from "@heroui/react";
import { PaymentMethodSchema } from "@/helpers/schemas";
import { editPaymentMethod } from "./actions";
import type { PaymentMethod } from "@/helpers/types";

interface EditPaymentMethodProps {
  method: PaymentMethod | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: (method: PaymentMethod) => void;
}

export function EditPaymentMethod({
  method,
  isOpen,
  onClose,
  onUpdated,
}: EditPaymentMethodProps) {
  const [error, setError] = useState<string | null>(null);

  if (!method) return null;

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
            <Formik
              key={method.id}
              initialValues={{
                name: method.name,
                type: method.type,
                currency: method.currency,
              }}
              validationSchema={PaymentMethodSchema}
              onSubmit={async (values, { setSubmitting }) => {
                setError(null);
                const result = await editPaymentMethod(method.id, {
                  name: values.name,
                  type: values.type as any,
                  currency: values.currency as any,
                });
                if (result.success) {
                  onUpdated(result.data);
                  onClose();
                } else {
                  setError(result.error.message);
                }
                setSubmitting(false);
              }}
            >
              {({
                values,
                errors,
                touched,
                setFieldValue,
                handleSubmit,
                isSubmitting,
              }) => (
                <form onSubmit={handleSubmit}>
                  <Modal.Header>
                    <Modal.Heading>Edit Payment Method</Modal.Heading>
                  </Modal.Header>
                  <Modal.Body className="flex flex-col gap-4">
                    <TextField
                      isInvalid={!!errors.name && !!touched.name}
                      value={values.name}
                      onChange={(v) => setFieldValue("name", v)}
                    >
                      <Label>Name</Label>
                      <Input />
                      {touched.name && errors.name && (
                        <FieldError>{errors.name}</FieldError>
                      )}
                    </TextField>

                    <Select.Root
                      selectedKey={values.type || null}
                      onSelectionChange={(key) =>
                        setFieldValue("type", String(key))
                      }
                      isInvalid={!!errors.type && !!touched.type}
                      fullWidth
                    >
                      <Label>Type</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select type...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.type && errors.type && (
                        <p className="text-xs text-danger">{errors.type}</p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="credit_card">
                            Credit Card
                          </ListBox.Item>
                          <ListBox.Item id="debit_card">
                            Debit Card
                          </ListBox.Item>
                          <ListBox.Item id="cash">Cash</ListBox.Item>
                          <ListBox.Item id="bank_transfer">
                            Bank Transfer
                          </ListBox.Item>
                          <ListBox.Item id="digital_wallet">
                            Digital Wallet
                          </ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    <Select.Root
                      selectedKey={values.currency || null}
                      onSelectionChange={(key) =>
                        setFieldValue("currency", String(key))
                      }
                      isInvalid={!!errors.currency && !!touched.currency}
                      fullWidth
                    >
                      <Label>Currency</Label>
                      <Select.Trigger>
                        <Select.Value>
                          {({ isPlaceholder, selectedText }: any) =>
                            isPlaceholder ? (
                              <span className="text-default-400">
                                Select currency...
                              </span>
                            ) : (
                              selectedText
                            )
                          }
                        </Select.Value>
                        <Select.Indicator />
                      </Select.Trigger>
                      {touched.currency && errors.currency && (
                        <p className="text-xs text-danger">{errors.currency}</p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="USD">USD</ListBox.Item>
                          <ListBox.Item id="MXN">MXN</ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    {error && <p className="text-sm text-danger">{error}</p>}
                  </Modal.Body>
                  <Modal.Footer className="gap-2">
                    <Button variant="ghost" onPress={onClose}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      isDisabled={isSubmitting}
                    >
                      {isSubmitting ? <Spinner size="sm" /> : "Save"}
                    </Button>
                  </Modal.Footer>
                </form>
              )}
            </Formik>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal.Root>
  );
}
