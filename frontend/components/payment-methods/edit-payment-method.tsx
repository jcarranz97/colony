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
                method_type: method.method_type,
                default_currency: method.default_currency,
              }}
              validationSchema={PaymentMethodSchema}
              onSubmit={async (values, { setSubmitting }) => {
                setError(null);
                const result = await editPaymentMethod(method.id, {
                  name: values.name,
                  method_type: values.method_type,
                  default_currency: values.default_currency,
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
                      selectedKey={values.method_type || null}
                      onSelectionChange={(key) =>
                        setFieldValue("method_type", String(key))
                      }
                      isInvalid={!!errors.method_type && !!touched.method_type}
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
                      {touched.method_type && errors.method_type && (
                        <p className="text-xs text-danger">
                          {errors.method_type}
                        </p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="debit" textValue="Debit">
                            Debit
                          </ListBox.Item>
                          <ListBox.Item id="credit" textValue="Credit">
                            Credit
                          </ListBox.Item>
                          <ListBox.Item id="cash" textValue="Cash">
                            Cash
                          </ListBox.Item>
                          <ListBox.Item id="transfer" textValue="Transfer">
                            Transfer
                          </ListBox.Item>
                        </ListBox>
                      </Select.Popover>
                    </Select.Root>

                    <Select.Root
                      selectedKey={values.default_currency || null}
                      onSelectionChange={(key) =>
                        setFieldValue("default_currency", String(key))
                      }
                      isInvalid={
                        !!errors.default_currency && !!touched.default_currency
                      }
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
                      {touched.default_currency && errors.default_currency && (
                        <p className="text-xs text-danger">
                          {errors.default_currency}
                        </p>
                      )}
                      <Select.Popover>
                        <ListBox>
                          <ListBox.Item id="USD" textValue="USD">
                            USD
                          </ListBox.Item>
                          <ListBox.Item id="MXN" textValue="MXN">
                            MXN
                          </ListBox.Item>
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
